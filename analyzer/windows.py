import subprocess
import platform
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import time

# Importamos las herramientas lógicas del archivo hermano utils.py
import utils

# Intentar importar el motor de Drag & Drop
try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False





class JdkInfoDialog(tk.Toplevel):
    """Ventana emergente personalizada que incluye 'Más Info'"""
    def __init__(self, parent):

        super().__init__(parent)
        self.title("Error de JDK en Gradle Detectado")
        self.geometry("500x380")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.cancelar)
        self.transient(parent)
        self.grab_set()
        
        self.resultado = False

        tk.Label(
            self, 
            text="⚠️ Conflicto de JDK Detectado", 
            font=("Segoe UI", 12, "bold"), 
            fg="#664d03", 
            bg="#fff3cd", 
            pady=8
        ).pack(fill="x")

        msg = ("Se ha detectado una ruta fija de JDK conflictiva dentro de '.gradle/config.properties'.\n\n"
               "Esto suele dejar el proyecto 'zombi' impidiendo que sincronice tras actualizar Android Studio "
               "o al importar proyectos de otras máquinas.")
        
        tk.Label(
            self, text=msg, font=("Segoe UI", 10), wraplength=460, justify="left", pady=15, padx=20
        ).pack()

        self.btn_info = tk.Button(
            self, text="❓ ¿Por qué ocurre esto? (Más Información)", 
            font=("Segoe UI", 9, "underline"), fg="#0d6efd", bd=0, cursor="hand2",
            command=self.mostrar_explicacion
        )
        self.btn_info.pack(pady=(0, 15))

        self.txt_explicacion = tk.Text(
            self, wrap="word", font=("Segoe UI", 9), bg="#f8f9fa", height=7, padx=10, pady=5
        )
        
        frame_botones = tk.Frame(self)
        frame_botones.pack(side="bottom", fill="x", pady=15, padx=20)

        tk.Button(frame_botones, text="Cancelar", width=12, command=self.cancelar, font=("Segoe UI", 10)).pack(side="right", padx=5)
        tk.Button(frame_botones, text="🔧 Reparar de forma segura", bg="#d1e7dd", fg="#0f5132", font=("Segoe UI", 10, "bold"), command=self.aceptar).pack(side="right", padx=5)

    def mostrar_explicacion(self):
        self.btn_info.pack_forget()
        self.geometry("500x500")
        self.txt_explicacion.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        detalle = (
            "¿Por qué falla?\n"
            "Android Studio a veces escribe la ruta absoluta de su Java interno (carpeta 'jbr') en tu proyecto. "
            "Si el IDE se actualiza, cambias de sistema operativo o compartes el código por Git, esa ruta "
            "deja de existir en tu PC. Gradle se confunde buscando un fantasma y rompe el build con errores crípticos.\n\n"
            "¿Qué hace la reparación?\n"
            "El script simplemente comentará (#) la línea conflictiva. Esto obligará a Gradle a buscar el Java limpio "
            "de tu sistema o el que tengas configurado globalmente en las opciones del IDE, resolviendo el bloqueo al instante."
        )
        self.txt_explicacion.insert("1.0", detalle)
        self.txt_explicacion.config(state="disabled")

    def aceptar(self):
        self.resultado = True
        self.destroy()

    def cancelar(self):
        self.resultado = False
        self.destroy()


class AnalyzerWindow:
    def __init__(self, master, volver_callback=None):
        self.root = master
        self.volver_callback = volver_callback
        self.root.resizable(True, True)

        self.animando_carga = False
        self.path_seleccionado = ""
       
        self.root.geometry("700x670") # Ancho x alto
        self.path_seleccionado = ""

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        if self.volver_callback:
            tk.Button(
                self.main_frame, text="⬅ Volver al Menú", command=self.regresar, font=("Segoe UI", 9)
            ).pack(anchor="w", padx=10, pady=5)

        tk.Label(self.main_frame, text="Suite de Diagnóstico Android Studio", font=("Segoe UI", 12, "bold")).pack(pady=(5, 5))

        # Drop Label
        self.drop_label = tk.Label(
            self.main_frame, text="Arrastre aquí la carpeta del proyecto Android o use el botón inferior",
            width=75, height=3, relief="groove", bg="#f4f4f4", fg="#666666", font=("Segoe UI", 9), justify="center"
        )
        self.drop_label.pack(pady=5)

        if DND_AVAILABLE:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self.on_drop)

        # Controles
        frame_controles = tk.Frame(self.main_frame)
        frame_controles.pack(pady=5)

        tk.Button(frame_controles, text="📁 Seleccionar Carpeta", command=self.seleccionar_carpeta, font=("Segoe UI", 9)).grid(row=0, column=0, padx=5)

        self.btn_analizar = tk.Button(
            frame_controles, text="🔍 Iniciar Análisis", command=self.iniciar_analisis_hilo,
            font=("Segoe UI", 9, "bold"), bg="#d1e7dd"
        )
        self.btn_analizar.grid(row=0, column=1, padx=5)

        # Consola
        frame_consola = tk.Frame(self.main_frame)
        frame_consola.pack(fill="both", expand=True, padx=15, pady=5)

        self.txt_salida = tk.Text(frame_consola, wrap="word", font=("Consolas", 10), bg="#212529", fg="#f8f9fa")
        scrollbar = tk.Scrollbar(frame_consola, command=self.txt_salida.yview)
        self.txt_salida.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.txt_salida.pack(side="left", fill="both", expand=True)

        self.txt_salida.tag_config("verde", foreground="#92ff92")
        self.txt_salida.tag_config("rojo", foreground="#ff6b6b")
        self.txt_salida.tag_config("amarillo", foreground="#ffd43b")
        self.txt_salida.tag_config("cian", foreground="#66d9ef", font=("Consolas", 10, "bold"))
        self.txt_salida.tag_config("titulo", foreground="#ffffff", font=("Consolas", 11, "bold"))

        # Acciones Rápidas
        self.frame_acciones = tk.Frame(self.main_frame)
        self.frame_acciones.pack(pady=10)

        self.btn_kill_emu = tk.Button(
            self.frame_acciones, text="💥 Forzar Cierre Emulador Zombie", command=self.reparar_emulador_gui,
            font=("Segoe UI", 9), bg="#f8d7da", fg="#842029", state="disabled"
        )
        self.btn_kill_emu.grid(row=0, column=0, padx=5)

        self.btn_force_restart = tk.Button(
            self.frame_acciones, text="🔄 Forzar Reinicio Máquina Virtual", command=self.ejecutar_force_restart_script,
            font=("Segoe UI", 9, "bold"), bg="#cff4fc", fg="#055160"
        )
        self.btn_force_restart.grid(row=0, column=1, padx=5)

        self.btn_clear_gradle = tk.Button(
            self.frame_acciones, text="🗑️ Vaciar Caché de Gradle", command=self.limpiar_cache_gradle_gui,
            font=("Segoe UI", 9), bg="#fff3cd", fg="#664d03"
        )
        self.btn_clear_gradle.grid(row=0, column=2, padx=5)


    def actualizar_animacion_carga(self):
        marcador = 0
        puntos = [".  ", ".. ", "...", "   "]
        
        while self.animando_carga:
            # Cambiamos el texto del botón de análisis para mostrar movimiento
            self.btn_analizar.config(text=f"Analizando{puntos[marcador]}")
            marcador = (marcador + 1) % len(puntos)
            time.sleep(0.3) # Velocidad del parpadeo
            
        # Cuando termine, restauramos el texto original del botón
        self.btn_analizar.config(text="Iniciar Análisis")


    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.actualizar_ruta(carpeta)

    def on_drop(self, event):
        ruta = event.data.strip("{}")
        self.actualizar_ruta(ruta)

    def actualizar_ruta(self, ruta):
        self.path_seleccionado = ruta
        self.drop_label.config(text=ruta, fg="black", wraplength=600)
        self.btn_analizar.config(state="normal")

    def log(self, texto, tag=None):
        self.txt_salida.insert(tk.END, texto + "\n", tag)
        self.txt_salida.see(tk.END)


    def iniciar_analisis_hilo(self):
        """Punto de entrada del botón: Configura la animación y arranca el hilo"""
        if self.animando_carga:
            return # Evita que pulsen el botón si ya está analizando

        # 1. Validar ruta antes de lanzar el hilo (para evitar hilos fantasma si da error)
        ruta_texto = self.path_seleccionado.strip() if self.path_seleccionado else ""
        if ruta_texto and not Path(ruta_texto).exists():
            messagebox.showerror("Error", "La ruta seleccionada no existe.")
            return

        # 2. Activar estados de carga
        self.animando_carga = True
        self.btn_analizar.config(state="disabled") # Desactivar temporalmente
        if hasattr(self, 'btn_buscar'): self.btn_buscar.config(state="disabled")

        # 3. Lanzar la animación en un hilo y el análisis en otro
        threading.Thread(target=self.actualizar_animacion_carga, daemon=True).start()
        threading.Thread(target=self._tarea_analisis_fondo, daemon=True).start()


    def _tarea_analisis_fondo(self):
        """Aquí dentro va TODA tu lógica actual de ejecutar_analisis"""
        try:
            ruta_texto = self.path_seleccionado.strip() if self.path_seleccionado else ""
            tiene_proyecto = bool(ruta_texto)
            if tiene_proyecto:
                root = Path(ruta_texto)

            # Habilitar la caja de texto desde el hilo de forma segura
            self.txt_salida.config(state="normal")
            self.txt_salida.delete("1.0", tk.END)

            self.log("==================================================", "cian")
            self.log("====== SUITE DE DIAGNÓSTICO ANDROID STUDIO ======", "titulo")
            self.log("==================================================", "cian")
            
            if tiene_proyecto:
                self.log(f"Ruta del proyecto: {root.resolve()}\n")
                self.log("--- 1. Análisis de Integridad del Proyecto ---", "cian")
                self.escanear_archivos_corruptos_gui(root)
                agp_detectado = utils.buscar_agp(root)
                kotlin_detectado = utils.buscar_kotlin(root)
            else:
                self.log("Modo: ANÁLISIS GLOBAL DEL ENTORNO (Sin proyecto seleccionado)\n")
                agp_detectado = "No detectado"
                kotlin_detectado = "No detectado"

            # (Continúa aquí con el resto de tus logs: Java, Android Studio, Emulador, Caché...)
            java_detectado = utils.detectar_java_version()
            as_detectado = utils.detectar_android_studio()
            as_viejo_detectado = utils.viejo_detectar_android_studio()

            if tiene_proyecto:
                self.log("\n--- 2. Datos del Proyecto (Build) ---", "cian")
                self.log(f"Android Gradle Plugin (AGP): {agp_detectado}", "verde" if agp_detectado != "No detectado" else "amarillo")
                self.log(f"Kotlin:                      {kotlin_detectado}", "verde" if kotlin_detectado != "No detectado" else "amarillo")

            self.log("\n--- 3. Entorno de Desarrollo & Java ---", "cian")
            self.log(f"Java (PATH):                 {java_detectado}", "verde" if "encontrado" not in java_detectado else "rojo")
            self.log(f"Android Studio (IDE):        {as_detectado}", "verde" if "no" not in as_detectado.lower() else "amarillo")
            self.log(as_viejo_detectado)
            self.log(f"Sistema Operativo:           {platform.system()} {platform.release()} ({platform.machine()})")

            if tiene_proyecto:
                self.log("\n--- 4. Diagnóstico de Compatibilidad Cruzada ---", "cian")
                comp_ide = utils.evaluar_compatibilidad(as_detectado, agp_detectado)
                self.log(comp_ide, "rojo" if "❌" in comp_ide else "verde")
                self.verificar_compatibilidad_java_agp_gui(java_detectado, agp_detectado)

            self.log("\n--- 5. Estado del Emulador Android ---", "cian")
            diagnostico_emulador, requiere_reinicio = utils.verificar_estado_emulador()
            self.log(diagnostico_emulador, "rojo" if requiere_reinicio else "verde")
            self.log(utils.verificar_configuracion_teclado_emulador())
            
            if requiere_reinicio:
                self.btn_kill_emu.config(state="normal")
                self.log("\n⚠️ Se ha detectado un bloqueo. Puedes usar el botón de abajo para aplicar un Hard-Kill.", "amarillo")
            else:
                self.btn_kill_emu.config(state="disabled")

            self.log("\n--- 6. Almacenamiento Caché de Gradle ---", "cian")
            self.calcular_cache_gradle_gui()

            self.log("\n==================================================", "cian")
            self.log("✨ Análisis finalizado con éxito.", "verde")
            self.log("==================================================", "cian")
            
        finally:
            # 4. AL TERMINAR (Pase lo que pase): Frenamos la animación y reactivamos controles
            self.animando_carga = False
            self.btn_analizar.config(state="normal")
            if hasattr(self, 'btn_buscar'): self.btn_buscar.config(state="normal")
            self.txt_salida.config(state="disabled")



    def escanear_archivos_corruptos_gui(self, root):
        archivos_clave = [
            root / "build.gradle.kts", root / "build.gradle",
            root / "gradle" / "libs.versions.toml",
            root / "settings.gradle.kts", root / "settings.gradle"
        ]
        errores = 0
        for archivo in archivos_clave:
            if archivo.exists():
                contenido = utils.leer_archivo(archivo)
                if "<<<<<<<" in contenido or "=======" in contenido or ">>>>>>>" in contenido:
                    self.log(f"❌ CONFLICTO DE GIT DETECTADO en: {archivo.name}", "rojo")
                    errores += 1
        if errores == 0:
            self.log("✅ No se detectaron conflictos de Git en los scripts de build.", "verde")

        config_path = root / ".gradle" / "config.properties"
        if config_path.exists():
            lineas = config_path.read_text(encoding="utf-8").splitlines()
            for i, linea in enumerate(lineas):
                if "java.home" in linea and "Android Studio" in linea and "jbr" in linea and not linea.strip().startswith("#"):
                    self.log(f"⚠️ Error de JDK en Gradle Detectado en config.properties", "amarillo")
                    
                    dialogo = JdkInfoDialog(self.root)
                    self.root.wait_window(dialogo)
                    
                    if dialogo.resultado:
                        lineas[i] = f"# Corregido por suite GUI: {lineas[i]}"
                        config_path.write_text("\n".join(lineas) + "\n", encoding="utf-8")
                        self.log("✨ Archivo config.properties reparado con éxito.", "verde")

    def verificar_compatibilidad_java_agp_gui(self, version_java_str, version_agp_str):
        v_java = utils.parsear_version(version_java_str)
        v_agp = utils.parsear_version(version_agp_str)
        if v_java == (0,0,0) or v_agp == (0,0,0):
            return
        
        req_java = 11
        if v_agp >= (9, 0, 0): req_java = 21
        elif v_agp >= (8, 0, 0): req_java = 17

        java_principal = v_java[0]
        if java_principal < req_java:
            self.log(f"❌ INCOMPATIBILIDAD DE JDK:\n   - AGP {version_agp_str} requiere Java {req_java}.\n   - Tu entorno tiene Java {java_principal}.", "rojo")
        else:
            self.log(f"✅ Versión de Java ({java_principal}) es compatible con AGP {version_agp_str}.", "verde")

    def calcular_cache_gradle_gui(self):
        gradle_cache = Path.home() / ".gradle" / "caches"
        if not gradle_cache.exists():
            self.log("ℹ️ No se detectó una carpeta de caché de Gradle global.")
            return
        try:
            total_bytes = sum(f.stat().st_size for f in gradle_cache.glob('**/*') if f.is_file())
            total_mb = total_bytes / (1024 * 1024)
            self.log(f"La caché global (.gradle/caches) ocupa: {total_mb:.2f} MB")
            if total_mb > 3072:
                self.log("⚠️ La caché supera los 3GB. Podría causar ralentizaciones o corrupciones.", "amarillo")
        except Exception:
            self.log("ℹ️ No se pudo calcular el tamaño completo (Archivos bloqueados en uso).")

    def ejecutar_force_restart_script(self):
        if messagebox.askyesno("Forzar Reinicio", "¿Estás seguro de que deseas forzar el reinicio de la máquina virtual?\n\nEsto ejecutará el script 'force_restart.py'."):
            try:
                ruta_script = Path(__file__).parent / "force_restart.py"
                if not ruta_script.exists():
                    messagebox.showerror("Error", f"No se pudo encontrar el archivo script en la ruta:\n{ruta_script}")
                    return

                import sys
                resultado = subprocess.run(
                    [sys.executable, str(ruta_script)], capture_output=True, text=True, timeout=15
                )

                if resultado.returncode == 0:
                    messagebox.showinfo("Éxito", "La máquina virtual se ha reiniciado correctamente.")
                    if self.path_seleccionado: self.iniciar_analisis_hilo()
                else:
                    error_msg = resultado.stderr or resultado.stdout
                    messagebox.showerror("Error en Script", f"El script terminó con errores:\n\n{error_msg}")
            except subprocess.TimeoutExpired:
                messagebox.showerror("Error", "El script 'force_restart.py' tardó demasiado tiempo en responder.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo ejecutar el script:\n{e}")

    def reparar_emulador_gui(self):
        if messagebox.askyesno("Forzar Cierre", "¿Estás seguro de que deseas matar forzosamente todos los emuladores colgados y reiniciar el servidor ADB?"):
            try:
                subprocess.run(["taskkill", "/F", "/IM", "qemu-system-x86_64.exe"], capture_output=True)
                subprocess.run(["taskkill", "/F", "/IM", "emulator.exe"], capture_output=True)
                adb_path = utils.buscar_adb()
                subprocess.run([adb_path, "kill-server"], capture_output=True)
                subprocess.run([adb_path, "start-server"], capture_output=True)
                messagebox.showinfo("Éxito", "Procesos limpiados. Reinicia el emulador desde Android Studio.")
                self.iniciar_analisis_hilo()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def limpiar_cache_gradle_gui(self):
        if messagebox.askyesno("Limpiar Caché", "¡ATENCIÓN!\nEsto eliminará la caché de Gradle global. Asegúrate de tener Android Studio cerrado por completo.\n\n¿Proceder con el borrado?"):
            gradle_cache = Path.home() / ".gradle" / "caches"
            if gradle_cache.exists():
                try:
                    import shutil
                    shutil.rmtree(gradle_cache)
                    messagebox.showinfo("Éxito", "Caché de Gradle eliminada correctamente.")
                    if self.path_seleccionado: self.iniciar_analisis_hilo()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar la caché por completo.\nDetalle: {e}")

    def regresar(self):
        if DND_AVAILABLE:
            self.root.drop_target_unregister()
        self.main_frame.destroy()
        self.volver_callback()