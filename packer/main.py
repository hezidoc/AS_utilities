import os
import zipfile
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


# ================== FUNCIÓN DE COMPRESIÓN ORIGINAL ==================
def comprimir_proyecto_android(path_proyecto, nombre_salida=None):
    if not os.path.exists(path_proyecto):
        raise FileNotFoundError(f"El path '{path_proyecto}' no existe.")

    exclude_dirs = {
        '.gradle', 'build', '.idea', '.cxx',
        'captures', '__pycache__', '.externalNativeBuild'
    }

    exclude_files = {
        'local.properties', '.DS_Store',
        'thumbs.db', 'desktop.ini'
    }

    with zipfile.ZipFile(nombre_salida, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for raiz, directorios, archivos in os.walk(path_proyecto):
            directorios[:] = [d for d in directorios if d not in exclude_dirs]

            for archivo in archivos:
                if archivo in exclude_files:
                    continue

                ruta_completa = os.path.join(raiz, archivo)
                ruta_relativa = os.path.relpath(ruta_completa, path_proyecto)
                zipf.write(ruta_completa, ruta_relativa)


# ================== CLASE DE LA INTERFAZ (COMO FRAME) ==================
class PackerWindow:
    def __init__(self, root, volver_callback=None):
        self.root = root
        self.volver_callback = volver_callback
        
        # Ajustamos el tamaño de la ventana contenedora
        self.root.geometry("650x440")
        self.path_seleccionado = ""

        # Creamos un Frame principal para envolver todo y poder destruirlo al salir
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Botón para regresar al menú principal (solo si venimos desde el main)
        if self.volver_callback:
            tk.Button(
                self.main_frame, 
                text="⬅ Volver al Menú", 
                command=self.regresar,
                font=("Segoe UI", 9)
            ).pack(anchor="w", padx=10, pady=5)

        tk.Label(
            self.main_frame,
            text="Proyecto Android Studio",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(5, 5))

        # --- ZONA DRAG & DROP ---
        self.drop_label = tk.Label(
            self.main_frame,
            text="Arrastre aquí la carpeta del proyecto\n\no seleccionala usando el botón",
            width=60,
            height=5,
            relief="groove",
            bg="#f4f4f4",
            fg="#666666",
            font=("Segoe UI", 10),
            justify="center"
        )
        self.drop_label.pack(pady=10)

        if DND_AVAILABLE:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self.on_drop)

        # --- BOTÓN SELECCIONAR ---
        tk.Button(
            self.main_frame,
            text="📁  Seleccionar carpeta",
            command=self.seleccionar_carpeta,
            font=("Segoe UI", 10),
            width=25
        ).pack(pady=5)

        # --- RADIO BUTTONS ---
        self.opcion_path = tk.StringVar(value="script")

        frame_radio = tk.Frame(self.main_frame)
        frame_radio.pack(pady=10)

        tk.Label(
            frame_radio,
            text="Ubicación del archivo ZIP:",
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        tk.Radiobutton(
            frame_radio,
            text="Path del script",
            variable=self.opcion_path,
            value="script"
        ).pack(anchor="w")

        tk.Radiobutton(
            frame_radio,
            text="Path del proyecto",
            variable=self.opcion_path,
            value="proyecto"
        ).pack(anchor="w")

        # --- BOTÓN FINAL ---
        tk.Button(
            self.main_frame,
            text="Comprimir proyecto",
            command=self.comprimir_desde_gui,
            font=("Segoe UI", 10, "bold"),
            height=2,
            width=30
        ).pack(pady=15)

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.actualizar_ruta(carpeta)

    def on_drop(self, event):
        ruta = event.data.strip("{}")
        self.actualizar_ruta(ruta)

    def actualizar_ruta(self, ruta):
        self.path_seleccionado = ruta
        self.drop_label.config(text=ruta, fg="black", wraplength=520)

    def comprimir_desde_gui(self):
        path = self.path_seleccionado.strip()
        if not path or not os.path.isdir(path):
            messagebox.showerror("Error", "Ruta de proyecto inválida")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        nombre_zip = f"proyecto_android_{timestamp}.zip"

        if self.opcion_path.get() == "script":
            salida = os.path.join(os.getcwd(), nombre_zip)
        else:
            carpeta_padre = os.path.dirname(path)
            salida = os.path.join(carpeta_padre, nombre_zip)

        try:
            comprimir_proyecto_android(path, salida)
            messagebox.showinfo("Éxito", f"Proyecto comprimido correctamente:\n\n{salida}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def regresar(self):
        # Desvinculamos el evento DnD para que no interfiera en otras pantallas
        if DND_AVAILABLE:
            self.root.drop_target_unregister()
        # Destruimos este menú completo
        self.main_frame.destroy()
        # Llamamos al menú principal para que se vuelva a dibujar
        self.volver_callback()


def iniciar_packer():
    root_class = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk
    ventana_raiz = root_class()
    app = PackerWindow(ventana_raiz)
    ventana_raiz.mainloop()

if __name__ == "__main__":
    iniciar_packer()