import os
import re
import platform
import subprocess
import json
from pathlib import Path

def parsear_version(version_str):
    try:
        numeros = re.findall(r'\d+', version_str)
        return tuple(map(int, numeros[:3]))
    except Exception:
        return (0, 0, 0)

def leer_archivo(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""

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
            return m.group(1)

    return "No detectado"

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

def viejo_detectar_android_studio():
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

def detectar_android_studio():
    # 1. Intentar detectar si viene por variables de entorno activas
    for var in ["IDEA_FULL_VERSION", "IDEA_VERSION"]:
        if var in os.environ:
            return f"Android Studio (entorno): {os.environ[var]}"
            
    # 2. Definir todas las rutas posibles de instalación en Windows/User
    localappdata = os.environ.get("LOCALAPPDATA", "")
    programfiles = os.environ.get("ProgramFiles", r"C:\Program Files")
    
    posibles_rutas = [
        Path(programfiles) / "Android" / "Android Studio",                      # Instalación Global estándar
        Path(localappdata) / "Android" / "Android Studio",                      # Instalación por usuario estándar
        Path(localappdata) / "Programs" / "Android Studio",                     # Variación de instalación local
        Path(localappdata) / "Programs" / "Android Studio1",                    # Copias de seguridad de parches
    ]
    
    for ruta in posibles_rutas:
        if ruta.exists():
            # ---- INTENTO 1: Leer el archivo product-info.json ----
            json_path = ruta / "product-info.json"
            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text(encoding="utf-8"))
                    version = data.get("version", "")
                    if version:
                        return f"Android Studio {version}"
                except Exception:
                    pass
            
            # ---- INTENTO 2: Leer bin/build.txt ----
            build_txt_path = ruta / "bin" / "build.txt"
            if build_txt_path.exists():
                try:
                    contenido_build = build_txt_path.read_text(encoding="utf-8").strip()
                    if contenido_build:
                        return f"Android Studio {contenido_build}"
                except Exception:
                    pass

            # ---- INTENTO 3 (EL DEFINITIVO): Preguntar a Windows la versión del .exe ----
            exe_64 = ruta / "bin" / "studio64.exe"
            if exe_64.exists():
                try:
                    # Usamos PowerShell para leer la propiedad ProductVersion directamente del ejecutable
                    cmd = f'(Get-Item "{exe_64}").VersionInfo.ProductVersion'
                    resultado = subprocess.run(
                        ["powershell", "-Command", cmd],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )
                    version_exe = resultado.stdout.strip()
                    if version_exe:
                        # Limpiamos posibles textos extras del build de JetBrains
                        return f"Android Studio {version_exe}"
                except Exception:
                    pass

            # ---- FALLBACK ----
            return "Android Studio detectado (Ruta localizada)"

    return "Android Studio no encontrado"

def buscar_adb():
    localappdata = os.environ.get("LOCALAPPDATA", "")
    ruta_estandar = os.path.join(localappdata, "Android", "Sdk", "platform-tools", "adb.exe")
    if os.path.exists(ruta_estandar):
        return ruta_estandar
    return "adb"

def verificar_estado_emulador():
    adb_path = buscar_adb()
    try:
        tasklist = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq qemu-system-x86_64.exe", "/FO", "CSV"],
            capture_output=True, text=True, timeout=3
        ).stdout
        emulador_corriendo = "qemu-system-x86_64.exe" in tasklist
    except Exception:
        emulador_corriendo = False

    if not emulador_corriendo:
        return "ℹ️ El emulador no se está ejecutando en segundo plano.", False

    try:
        resultado = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=5)
        salida = resultado.stdout
        
        if "emulator" in salida:
            if "offline" in salida:
                return "❌ ALERTA: El emulador está colgado (Estado: OFFLINE). Requiere reinicio.", True
            
            ping_emulador = subprocess.run(
                [adb_path, "shell", "getprop", "sys.boot_completed"],
                capture_output=True, text=True, timeout=4
            )
            if ping_emulador.returncode != 0 or not ping_emulador.stdout.strip():
                return "❌ ALERTA: El proceso responde a ADB pero el sistema operativo interno está congelado.", True
                
            return "✅ El emulador está encendido y respondiendo correctamente.", False
        else:
            return "❌ ALERTA: El proceso del emulador existe en Windows, pero ADB no lo detecta (Zombi).", True
    except Exception:
        return "⚠️ ADB bloqueado o no encontrado. No se puede verificar la salud del emulador.", False

def evaluar_compatibilidad(version_as, version_agp):
    if "No detectado" in version_as or version_agp == "No detectado":
        return "⚠️ No se puede calcular la compatibilidad (Faltan datos)."

    # Extraer la versión clave (Ej: "2025.3" o "2024.1")
    m_ai = re.search(r'AI-(\d{2})(\d{1})', version_as)
    if m_ai:
        clave_as = f"20{m_ai.group(1)}.{m_ai.group(2)}"
    else:
        m_as = re.search(r'(\d{4}\.\d+)', version_as)
        if m_as:
            clave_as = m_as.group(1)
        else:
            return "⚠️ Formato de versión de Android Studio no reconocido para diagnóstico."
    
    # Tabla oficial y actualizada de compatibilidad estricta (AS vs AGP Máximo Nativo/Recomendado)
    # Nota: Android Studio suele soportar su versión AGP homóloga nativa perfectamente.
    tabla_compatibilidad = {
        "2026.1": "9.3.0",
        "2025.3": "9.2.0",
        "2025.2": "9.1.0",
        "2025.1": "9.0.0",
        "2024.2": "8.7.0",
        "2024.1": "8.5.0",
        "2023.3": "8.5.0",
        "2023.2": "8.4.0",
        "2023.1": "8.3.0"
    }

    # Si la versión es muy nueva y no está en la tabla, hacemos una estimación lógica flexible
    if clave_as in tabla_compatibilidad:
        agp_maximo_soportado = tabla_compatibilidad[clave_as]
    else:
        try:
            año_as, release_as = map(int, clave_as.split('.'))
            if año_as >= 2025:
                # Reajuste de la estimación para la era AGP 9.x+
                mayor = 9 + (año_as - 2025)
                menor = release_as - 1
                agp_maximo_soportado = f"{mayor}.{menor}.0"
            else:
                agp_maximo_soportado = "8.8.0"
        except Exception:
            agp_maximo_soportado = "9.0.0"

    v_actual_agp = parsear_version(version_agp)
    v_max_agp = parsear_version(agp_maximo_soportado)

    # Permitir una tolerancia: Android Studio suele aceptar AGPs ligeramente superiores en parches (X.X.ga)
    # Comprobación estricta de versiones mayores primero
    if v_actual_agp[0] > v_max_agp[0] or (v_actual_agp[0] == v_max_agp[0] and v_actual_agp[1] > v_max_agp[1]):
        return (
            f"❌ INCOMPATIBILIDAD DETECTADA\n"
            f"   - Tu Android Studio actual (Basado en {clave_as}) está estimado para soportar hasta AGP {agp_maximo_soportado}.\n"
            f"   - El proyecto requiere una versión superior: AGP {version_agp}.\n\n"
            f"     💡 RECOMENDACIÓN: Actualiza tu Android Studio o baja el AGP a '{agp_maximo_soportado}' en los scripts de build."
        )
    else:
        return f"✅ El entorno de Android Studio ({clave_as}) es compatible con el AGP {version_agp} del proyecto."
    
def verificar_configuracion_teclado_emulador():
    """
    Inspecciona los perfiles de los emuladores instalados (AVDs) 
    para verificar si tienen habilitada la entrada de teclado físico.
    """
    user_home = Path(os.environ.get("USERPROFILE", ""))
    ruta_avd = user_home / ".android" / "avd"
    
    if not ruta_avd.exists():
        return "ℹ️ No se encontró la ruta estándar de perfiles AVD (.android/avd)."

    alertas = []
    # Buscar todos los archivos de configuración de los emuladores (.avd/config.ini)
    archivos_config = list(ruta_avd.glob("**/*.avd/config.ini"))
    
    if not archivos_config:
        return "ℹ️ No se detectaron emuladores creados para analizar su configuración."

    for config_path in archivos_config:
        nombre_emulador = config_path.parent.stem
        contenido = leer_archivo(config_path)
        
        # Buscar la propiedad que controla el teclado físico del PC
        # hw.keyboard = yes (Permite escribir con el teclado de la PC)
        # hw.keyboard = no  (Fuerza a usar el teclado en pantalla de Android)
        m_teclado = re.search(r'hw\.keyboard\s*=\s*(yes|no)', contenido, re.IGNORECASE)
        
        if m_teclado:
            estado = m_teclado.group(1).lower()
            if estado == "no":
                reparar_teclado_emuladores()
                alertas.append(f"❌ El emulador '{nombre_emulador}' tiene el teclado físico DESACTIVADO (hw.keyboard=no).")
        else:
            # Por defecto en algunas versiones si no existe la línea, podría no mapearlo correctamente
            alertas.append(f"⚠️ El emulador '{nombre_emulador}' no tiene definida la propiedad 'hw.keyboard'. Podría fallar.")

    if alertas:
        return "\n".join(alertas)
    return "✅ Todos los emuladores configurados tienen el soporte de teclado físico activo (hw.keyboard=yes)."


def reparar_teclado_emuladores():
    """
    Busca todos los emuladores creados en la PC y fuerza 
    la activación del teclado físico en sus archivos config.ini
    """
    user_home = Path(os.environ.get("USERPROFILE", ""))
    ruta_avd = user_home / ".android" / "avd"
    alertas = []

    
    if not ruta_avd.exists():
        alertas.append("❌ No se encontró la carpeta de configuración de emuladores (.android/avd).")
        return False

    archivos_config = list(ruta_avd.glob("**/*.avd/config.ini"))
    
    if not archivos_config:
        alertas.append("ℹ️ No se encontraron emuladores instalados para reparar.")
        return False

    alertas.append(f"🔍 Se encontraron {len(archivos_config)} emulador(es). Iniciando reparación...")
    alertas.append("-" * 50)

    for config_path in archivos_config:
        nombre_emulador = config_path.parent.stem
        contenido = leer_archivo(config_path)
        
        if not contenido:
            alertas.append(f"⚠️ No se pudo leer el archivo de {nombre_emulador}. Saltando...")
            continue

        modificado = False

        # 1. Reparar o añadir hw.keyboard
        if "hw.keyboard" in contenido:
            # Si existe pero está en 'no', lo cambiamos a 'yes'
            if re.search(r'hw\.keyboard\s*=\s*no', contenido, re.IGNORECASE):
                contenido = re.sub(r'hw\.keyboard\s*=\s*no', 'hw.keyboard=yes', contenido, flags=re.IGNORECASE)
                modificado = True
        else:
            # Si no existe la propiedad, la añadimos al final
            contenido += "\nhw.keyboard=yes"
            modificado = True

        # 2. Reparar o añadir hw.keyboard.lid (el sensor que detecta si el teclado está expuesto)
        if "hw.keyboard.lid" in contenido:
            if re.search(r'hw\.keyboard\.lid\s*=\s*no', contenido, re.IGNORECASE):
                contenido = re.sub(r'hw\.keyboard\.lid\s*=\s*no', 'hw.keyboard.lid=yes', contenido, flags=re.IGNORECASE)
                modificado = True
        else:
            contenido += "\nhw.keyboard.lid=yes"
            modificado = True

        # Guardar los cambios solo si fue necesario modificarlos
        if modificado:
            try:
                config_path.write_text(contenido, encoding="utf-8")
                alertas.append(f"✅ ¡Reparado con éxito!: '{nombre_emulador}' ahora tiene el teclado habilitado.")
            except Exception as e:
                alertas.append(f"❌ Error al escribir en el emulador {nombre_emulador}: {e}")
        else:
            alertas.append(f"✨ El emulador '{nombre_emulador}' ya tenía la configuración de teclado correcta.")

    alertas.append("-" * 50)
    alertas.append("💡 NOTA IMPORTANTE: Si el emulador estaba abierto, ciérralo por completo")
    alertas.append("   y ejecútalo usando 'Cold Boot Now' (Arranque en frío) desde Android Studio")
    alertas.append("   para que cargue la nueva configuración de hardware.")
    if alertas:
        return "\n".join(alertas)
    return True