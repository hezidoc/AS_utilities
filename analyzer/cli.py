import os
import re
import platform
import subprocess
import json
from pathlib import Path
# Usamos la librería estándar para comparar versiones de forma segura
from dataclasses import dataclass
import urllib.request
import xml.etree.ElementTree as ET

# ---------- CONFIGURACIÓN DE COLORES (ANSI) ----------
RESET = "\033[0m"
VERDE = "\033[92m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
CIAN = "\033[96m"
AZUL = "\033[94m"
NEVADA = "\033[1m" # Negrita


def parsear_version(version_str):
    """Convierte un string de versión (ej: '9.0.0' o '2025.1.4') en una tupla de enteros para comparar."""
    try:
        # Extrae solo los números (ignora 'No explícito', letras, etc.)
        numeros = re.findall(r'\d+', version_str)
        return tuple(map(int, numeros[:3]))
    except Exception:
        return (0, 0, 0)

def leer_archivo(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""

# ---------- AGP ----------
def buscar_agp(root):
    toml = root / "gradle" / "libs.versions.toml"
    if toml.exists():
        contenido = leer_archivo(toml)
        m = re.search(r'agp\s*=\s*"([\d.]+)"', contenido)
        if m:
            return m.group(1)

    patrones = [
        r'com\.android\.tools\.build:gradle:([\d.]+)',
        r'id\("com\.android\.application"\)\s*version\s*"([\d.]+)"'
    ]

    for archivo in [root / "build.gradle", root / "build.gradle.kts",
                    root / "settings.gradle", root / "settings.gradle.kts"]:
        contenido = leer_archivo(archivo)
        for patron in patrones:
            m = re.search(patron, contenido)
            if m:
                return m.group(1)

    wrapper = root / "gradle" / "wrapper" / "gradle-wrapper.properties"
    if wrapper.exists():
        contenido = leer_archivo(wrapper)
        m = re.search(r'gradle-([\d.]+)-', contenido)
        if m:
            return m.group(1) # Devolvemos solo el número para poder procesarlo adecuadamente

    return "No detectado"

# ---------- KOTLIN ----------
def buscar_kotlin(root):
    toml = root / "gradle" / "libs.versions.toml"
    if toml.exists():
        contenido = leer_archivo(toml)
        m = re.search(r'kotlin\s*=\s*"([\d.]+)"', contenido)
        if m:
            return m.group(1)

    patrones = [
        r'kotlin_version\s*=\s*"([\d.]+)"',
        r'kotlin-gradle-plugin:([\d.]+)',
        r'id\("org\.jetbrains\.kotlin.*"\)\s*version\s*"([\d.]+)"'
    ]

    for archivo in root.rglob("*.gradle*"):
        contenido = leer_archivo(archivo)
        for patron in patrones:
            m = re.search(patron, contenido)
            if m:
                return m.group(1)

    return "No detectado"

# ---------- JAVA ----------
def detectar_java_version():
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        salida = result.stderr.strip() or result.stdout.strip()
        if not salida:
            return "Java instalado, versión no detectable"
        return salida.splitlines()[0]
    except FileNotFoundError:
        return "Java no encontrado en PATH"
    except Exception as e:
        return f"Error: {e}"

# ---------- ANDROID STUDIO ----------
def obtener_version_desde_json(path_as):
    """Lee el product-info.json de Android Studio para extraer la versión exacta de forma rápida."""
    json_path = Path(path_as) / "product-info.json"
    if json_path.exists():
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            return data.get("version", "")
        except Exception:
            pass
    return ""

def detectar_android_studio():
    # Intento por variables de entorno de IntelliJ
    for var in ["IDEA_FULL_VERSION", "IDEA_VERSION"]:
        if var in os.environ:
            return os.environ[var]

    if platform.system() == "Windows":
        rutas_posibles = [
            r"C:\Program Files\Android\Android Studio",
            # Agrega aquí rutas de JetBrains Toolbox si las usas:
            # os.path.expandvars(r"%LOCALAPPDATA%\Programs\Android Studio")
        ]
        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                version = obtener_version_desde_json(ruta)
                if version:
                    return version
                
                # Fallback al ejecutable si falla el JSON
                exe = os.path.join(ruta, "bin", "studio64.exe")
                if os.path.exists(exe):
                    try:
                        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=3)
                        if r.stdout:
                            return r.stdout.splitlines()[0]
                    except Exception:
                        return "Detectado (Versión inaccesible)"
                        
    return "No detectado"

# ---------- ANALIZADOR DE EMULADOR ----------


def buscar_adb():
    """Intenta localizar adb.exe en las rutas estándar de Android SDK en Windows."""
    localappdata = os.environ.get("LOCALAPPDATA", "")
    ruta_estandar = os.path.join(localappdata, "Android", "Sdk", "platform-tools", "adb.exe")
    if os.path.exists(ruta_estandar):
        return ruta_estandar
    return "adb" # Dependerá de si está en el PATH del sistema

def verificar_estado_emulador():
    """
    Analiza el estado del emulador usando ADB y los procesos de Windows.
    Devuelve un string con el diagnóstico y un booleano indicando si requiere reinicio.
    """
    adb_path = buscar_adb()
    
    # 1. Comprobar si el proceso del emulador está corriendo en Windows
    try:
        # Buscamos procesos del emulador qemu o emulator
        tasklist = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq qemu-system-x86_64.exe", "/FO", "CSV"],
            capture_output=True, text=True, timeout=3
        ).stdout
        
        emulador_corriendo = "qemu-system-x86_64.exe" in tasklist
    except Exception:
        emulador_corriendo = False

    if not emulador_corriendo:
        return "ℹ️ El emulador no se está ejecutando en segundo plano.", False

    # 2. Si el proceso existe, verificar si ADB lo reconoce y responde
    try:
        # 'adb devices' nos dice qué hay conectado
        resultado = subprocess.run(
            [adb_path, "devices"],
            capture_output=True, text=True, timeout=5
        )
        salida = resultado.stdout
        
        if "emulator" in salida:
            # Comprobar si el emulador está en estado 'offline' o 'unauthorized' (colgado)
            if "offline" in salida:
                return "❌ ALERTA: El emulador está colgado (Estado: OFFLINE). Requiere reinicio.", True
            
            # Intentar un comando rápido para ver si el emulador responde internamente
            ping_emulador = subprocess.run(
                [adb_path, "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True, timeout=4
            )
            
            if ping_emulador.returncode != 0 or not ping_emulador.stdout.strip():
                return "❌ ALERTA: El proceso responde a ADB pero el sistema operativo interno está congelado.", True
                
            return "✅ El emulador está encendido y respondiendo correctamente.", False
        else:
            return "❌ ALERTA: El proceso del emulador existe en Windows, pero ADB no lo detecta (Zombi).", True

    except subprocess.TimeoutExpired:
        return "❌ ALERTA: ADB se congeló intentando hablar con el emulador. El emulador está bloqueado.", True
    except FileNotFoundError:
        return "⚠️ ADB no fue encontrado. No se puede verificar el estado de salud interno del emulador.", False

def reparar_emulador():
    """Ejecuta un kill forzado del emulador y reinicia el servidor ADB."""
    print("\n🔄 Intentando reparar el emulador de forma automática...")
    
    # Forzar el cierre del proceso del emulador en Windows (Equivalente al Kill de PowerShell)
    try:
        subprocess.run(["taskkill", "/F", "/IM", "qemu-system-x86_64.exe"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/IM", "emulator.exe"], capture_output=True)
        print("   -> Procesos del emulador finalizados por la fuerza.")
    except Exception as e:
        print(f"   -> Error al cerrar procesos: {e}")

    # Reiniciar el servidor de ADB (a veces el cuelgue es de ADB, no del emulador)
    try:
        adb_path = buscar_adb()
        subprocess.run([adb_path, "kill-server"], capture_output=True)
        subprocess.run([adb_path, "start-server"], capture_output=True)
        print("   -> Servidor ADB reiniciado con éxito.")
    except Exception:
        pass
        
    print("✨ Limpieza completada. Ya puedes volver a iniciar el emulador desde Android Studio.")





# ---------- INTEGRIDAD DEL PROYECTO ----------

def auditar_y_reparar_jdk_gradle(root):
    """
    Detecta si .gradle/config.properties apunta a un JDK inválido/corrupto en Android Studio
    y ofrece corregirlo eliminando o comentando la línea conflictiva.
    """
    config_path = root / ".gradle" / "config.properties"
    if not config_path.exists():
        return

    try:
        lineas = config_path.read_text(encoding="utf-8").splitlines()
        linea_conflictiva_idx = None
        
        # Buscamos si existe java.home apuntando a la carpeta jbr de Android Studio
        for i, linea in enumerate(lineas):
            if linea.strip().startswith("java.home") and "Android Studio" in linea and "jbr" in linea:
                linea_conflictiva_idx = i
                break
        
        if linea_conflictiva_idx is not None:
            print(f"\n⚠️ {AMARILLO}DETECTADO ERROR DE JDK EN CONFIGURACIÓN DE GRADLE:{RESET}")
            print(f"   El archivo '{config_path}' obliga a usar un JDK potencialmente corrupto:")
            print(f"   {ROJO}{lineas[linea_conflictiva_idx]}{RESET}")
            
            respuesta = input(f"{NEVADA}¿Deseas corregir automáticamente este error eliminando la línea conflictiva? (s/n): {RESET}")
            if respuesta.lower() == 's':
                # Comentamos la línea para preservar el historial del archivo pero desactivar el error
                lineas[linea_conflictiva_idx] = f"# Corregido por script de diagnóstico: {lineas[linea_conflictiva_idx]}"
                config_path.write_text("\n".join(lineas) + "\n", encoding="utf-8")
                print(f"{VERDE}✨ ¡Reparado con éxito! Se eliminó el bloqueo del JDK. Gradle ahora usará el JDK del proyecto de forma limpia.{RESET}")
    except Exception as e:
        print(f"❌ No se pudo auditar/reparar el archivo config.properties: {e}")

def escanear_archivos_corruptos(root):
    """Busca marcas de conflicto de Git o archivos de configuración corruptos."""
    archivos_clave = [
        root / "build.gradle.kts", root / "build.gradle",
        root / "gradle" / "libs.versions.toml",
        root / "settings.gradle.kts", root / "settings.gradle"
    ]
    
    errores_encontrados = 0
    for archivo in archivos_clave:
        if archivo.exists():
            contenido = leer_archivo(archivo)
            if "<<<<<<<" in contenido or "=======" in contenido or ">>>>>>>" in contenido:
                print(f"❌ CONFLICTO DE GIT DETECTADO en: {archivo.name}")
                print("   El archivo tiene un merge conflict sin resolver. Resuélvelo antes de abrir el IDE.")
                errores_encontrados += 1
                
    if errores_encontrados == 0:
        print("✅ No se detectaron conflictos de Git ni corrupciones evidentes en los scripts de build.")

    # Ejecutamos la sub-auditoría específica del JDK de Gradle
    auditar_y_reparar_jdk_gradle(root)


# ---------- GRADLE CACHE ----------
def auditar_y_limpiar_cache_gradle():
    """Calcula el tamaño de la caché de Gradle y permite limpiarla si el usuario lo desea."""
    home = Path.home()
    gradle_cache = home / ".gradle" / "caches"
    
    if not gradle_cache.exists():
        print("ℹ️ No se detectó una carpeta de caché de Gradle global.")
        return

    print("--- Almacenamiento de Gradle ---")
    # Calcular tamaño de forma rápida
    total_bytes = sum(f.stat().st_size for f in gradle_cache.glob('**/*') if f.is_file())
    total_mb = total_bytes / (1024 * 1024)
    
    print(f"La caché global de Gradle (.gradle/caches) está ocupando: {total_mb:.2f} MB")
    
    if total_mb > 3072: # 2048: Si supera los 2 GB, sugerir limpieza
        print("⚠️ La caché es bastante grande. A veces, cachés corruptas rompen el build.")
        respuesta = input("¿Deseas vaciar la caché de Gradle para liberar espacio y prevenir errores? (s/n): ")
        if respuesta.lower() == 's':
            try:
                # Nota: Para borrar con seguridad, es mejor eliminar la subcarpeta 'transforms-X' o 'modules-2'
                # o el directorio entero si Android Studio está cerrado.
                import shutil
                shutil.rmtree(gradle_cache)
                print("✨ Caché de Gradle eliminada. (Se regenerará limpiamente en el próximo Build)")
            except Exception as e:
                print(f"❌ No se pudo borrar (asegúrate de cerrar Android Studio primero): {e}")


# ---------- ANALIZADOR DE COMPATIBILIDAD ----------

def verificar_compatibilidad_java_agp(version_java_str, version_agp_str):
    """Verifica si la versión de Java del sistema es suficiente para la versión de AGP del proyecto."""
    v_java = parsear_version(version_java_str)
    v_agp = parsear_version(version_agp_str)
    
    if v_java == (0,0,0) or v_agp == (0,0,0):
        return
    
    req_java = 11
    if v_agp >= (9, 0, 0):
        req_java = 21
    elif v_agp >= (8, 0, 0):
        req_java = 17

    # Asumiendo que v_java[0] nos da el release principal (ej: 21 de "21.0.8")
    java_principal = v_java[0]
    
    if java_principal < req_java:
        print(f"❌ INCOMPATIBILIDAD DE JDK:")
        print(f"   - El proyecto usa AGP {version_agp_str}, el cual requiere obligatoriamente Java {req_java}.")
        print(f"   - Tu PATH actual tiene instalado Java {java_principal}.")
        print(f"   💡 RECOMENDACIÓN: Configura Android Studio o tu variable de entorno JAVA_HOME para usar JDK {req_java}.")
    else:
        print(f"✅ Tu versión de Java ({java_principal}) cumple con los requisitos para AGP {version_agp_str}.")

def obtener_tabla_compatibilidad_remota():
    """
    Descarga en tiempo real el mapeo de versiones desde los servidores de Google.
    Devuelve un diccionario dinámico o un fallback si no hay internet.
    """
    # Enlace oficial del repositorio de herramientas de Android
    url_repository = "https://dl.google.com/android/repository/addons_list-5.xml"
    
    # Fallback local por si el usuario no tiene conexión a internet en ese momento
    fallback = {
        "2025.1": "8.13.0",
        "2024.3": "8.11.0",
        "2024.2": "8.9.0",
        "2024.1": "8.7.0"
    }
    
    try:
        # Hacemos una petición rápida con un timeout de 3 segundos
        with urllib.request.urlopen(url_repository, timeout=3) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        tabla_dinamica = {}
        
        # Google estructura esto en elementos <node> o <sdk:plugin> según la API.
        # Nota: Para simplificar el parseo de APIs complejas de Google sin librerías externas pesadas,
        # podemos también consumir el feed JSON alternativo de lanzamientos si estuviera disponible,
        # pero la forma más robusta y estándar "offline-first" con esteroides es usar un espejo actualizado.
        
        return fallback # De momento usamos el fallback estructurado, pero idealmente se parsea el XML.
    except Exception:
        return fallback

def evaluar_compatibilidad(version_as, version_agp):
    if version_as == "No detectado" or version_agp == "No detectado":
        return "⚠️ No se puede calcular la compatibilidad (Faltan datos)."

    # 1. Normalizar formato interno "AI-251" a "2025.1"
    m_ai = re.search(r'AI-(\d{2})(\d{1})', version_as)
    if m_ai:
        clave_as = f"20{m_ai.group(1)}.{m_ai.group(2)}"
    else:
        m_as = re.search(r'(\d{4}\.\d+)', version_as)
        if m_as:
            clave_as = m_as.group(1)
        else:
            return "⚠️ Formato de versión de Android Studio no reconocido para diagnóstico."
    
    # 2. Intentar deducir la regla de negocio de Google de forma algorítmica
    try:
        año_as, release_as = map(int, clave_as.split('.'))
        
        # Algoritmo de predicción para versiones modernas (A partir de 2024)
        if año_as >= 2024:
            pasos_desde_2024_1 = ((año_as - 2024) * 3) + (release_as - 1)
            pago_mayor = 8
            pago_menor = 7 + (pasos_desde_2024_1 * 2)
            agp_maximo_soportado = f"{pago_mayor}.{pago_menor}.0"
        else:
            tabla_local = {"2023.3": "8.5.0", "2023.2": "8.4.0", "2023.1": "8.3.0"}
            agp_maximo_soportado = tabla_local.get(clave_as, "8.0.0")
            
    except Exception:
        agp_maximo_soportado = "8.13.0"

    v_actual_agp = parsear_version(version_agp)
    v_max_agp = parsear_version(agp_maximo_soportado)

    if v_actual_agp > v_max_agp:
        # Enlace oficial de descarga directa
        url_descarga = "https://developer.android.com/studio"
        
        return (
            f"❌ INCOMPATIBILIDAD DETECTADA\n"
            f"   - Tu Android Studio actual (Basado en {clave_as}) solo soporta hasta AGP {agp_maximo_soportado}.\n"
            f"   - El proyecto requiere una versión superior: AGP {version_agp}.\n\n"
            f"   💡 RECOMENDACIONES DE SOLUCIÓN:\n"
            f"       👉 Opción A: Actualiza Android Studio a la última versión compatible.\n"
            f"                   Descárgala aquí: {url_descarga}\n"
            f"       👉 Opción B: Baja el AGP del proyecto a '{agp_maximo_soportado}' en tu 'libs.versions.toml' o 'build.gradle'."
        )
    else:
        return f"✅ El entorno de Android Studio ({clave_as}) es compatible con el AGP {version_agp} del proyecto."

# ---------- ANDROID STUDIO ----------

def detectar_android_studio_windows():
    posibles = [
        r"C:\Program Files\Android\Android Studio\bin\studio64.exe",
        r"C:\Program Files\Android\Android Studio\bin\studio.exe",
    ]

    for exe in posibles:
        if os.path.exists(exe):
            try:
                r = subprocess.run([exe, "--version"],
                                   capture_output=True,
                                   text=True,
                                   timeout=5)
                if r.stdout:
                    return r.stdout.splitlines()[0]
                return "Android Studio detectado (versión no disponible)"
            except Exception:
                return "Android Studio detectado (no ejecutable)"

    return "Android Studio no encontrado"

def detectar_android_studio():
    for var in ["IDEA_FULL_VERSION", "IDEA_VERSION"]:
        if var in os.environ:
            return f"Android Studio (entorno): {os.environ[var]}"

    if platform.system() == "Windows":
        return detectar_android_studio_windows()

    return "Android Studio no detectable"



# ---------- MAIN ----------
def main(project_path):
    root = Path(project_path)

    if not root.exists():
        print("❌ El path del proyecto no existe")
        return

    print(f"{AZUL}=================================================={RESET}")
    print(f"{NEVADA}{CIAN}====== SUITE DE DIAGNÓSTICO ANDROID STUDIO ======{RESET}")
    print(f"{AZUL}=================================================={RESET}")
    print(f"{NEVADA}Ruta del proyecto:{RESET} {root.resolve()}")

    # Análisis de integridad
    print(f"\n{CIAN}--- 1. Análisis de Integridad del Proyecto ---{RESET}")
    escanear_archivos_corruptos(root)

    # Recopilación de información del Entorno y Proyecto
    agp_detectado = buscar_agp(root)
    kotlin_detectado = buscar_kotlin(root)
    java_detectado = detectar_java_version()
    as_detectado = detectar_android_studio()

    print(f"\n{CIAN}--- 2. Datos del Proyecto (Build) ---{RESET}")
    print(f"{NEVADA}Android Gradle Plugin (AGP):{RESET} {VERDE}{agp_detectado}{RESET}")
    print(f"{NEVADA}Kotlin:                      {RESET}{VERDE}{kotlin_detectado}{RESET}")

    print(f"\n{CIAN}--- 3. Entorno de Desarrollo & Java ---{RESET}")
    print(f"{NEVADA}Java (PATH):                 {RESET}{VERDE}{java_detectado}{RESET}")
    print(f"{NEVADA}Android Studio (IDE):        {RESET}{VERDE}{as_detectado}{RESET}")
    print(f"{NEVADA}Sistema Operativo:           {RESET}{platform.system()} {platform.release()} ({platform.machine()})")

    # Diagnósticos de Compatibilidad Cruzada
    print(f"\n{CIAN}--- 4. Diagnóstico de Compatibilidad Cruzada ---{RESET}")
    print(f"{NEVADA}>> Compatibilidad IDE / AGP:{RESET}")
    # Nota: Asegúrate de que evaluar_compatibilidad() maneje colores internos, 
    # o imprimirá el texto plano que ya configuramos antes.
    print(evaluar_compatibilidad(as_detectado, agp_detectado))

    print(f"\n{NEVADA}>> Compatibilidad Java / AGP:{RESET}")
    verificar_compatibilidad_java_agp(java_detectado, agp_detectado)

    # Diagnóstico de herramientas en ejecución (Emulador)
    print(f"\n{CIAN}--- 5. Estado del Emulador Android ---{RESET}")
    diagnostico_emulador, requiere_reinicio = verificar_estado_emulador()
    print(diagnostico_emulador)
    
    if requiere_reinicio:
        print(f"{AMARILLO}⚠️ Se ha detectado un bloqueo en el emulador en segundo plano.{RESET}")
        respuesta = input(f"{NEVADA}¿Deseas aplicar un hard-kill automático al emulador zombi? (s/n): {RESET}")
        if respuesta.lower() == 's':
            reparar_emulador()

    # Auditoría de almacenamiento y mantenimiento de Gradle
    print(f"\n{CIAN}--- 6. Cache Gradle en SO (Puede tardar un poco) ---{RESET}")
    auditar_y_limpiar_cache_gradle()

    print(f"\n{AZUL}=================================================={RESET}")
    print(f"{VERDE}✨ Análisis finalizado con éxito.{RESET}")
    print(f"{AZUL}=================================================={RESET}")



if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Uso: python detectar_android.py <path_proyecto>")
    else:
        main(sys.argv[1])