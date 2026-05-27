# main.py (En la raíz de tu proyecto - AS_utilities/main.py)
import os
import sys
import tkinter as tk
from tkinter import messagebox

# 1. Localizamos la raíz donde se está ejecutando este script
directorio_raiz = os.path.dirname(os.path.abspath(__file__))

# 2. Registramos las subcarpetas de forma absoluta en el sistema para evitar fallos de ruta
carpeta_analyzer = os.path.join(directorio_raiz, "analyzer")
if carpeta_analyzer not in sys.path:
    sys.path.insert(0, carpeta_analyzer)

carpeta_screenmaker = os.path.join(directorio_raiz, "screenMaker")
if carpeta_screenmaker not in sys.path:
    sys.path.insert(0, carpeta_screenmaker)

# 3. Registramos también la raíz por si packer lo necesita
if directorio_raiz not in sys.path:
    sys.path.insert(0, directorio_raiz)


# --- IMPORTACIONES DE ENTORNO ---
try:
    from tkinterdnd2 import TkinterDnD
    DND_MAIN_AVAILABLE = True
except ImportError:
    DND_MAIN_AVAILABLE = False

try:
    from packer.main import PackerWindow
except ImportError:
    PackerWindow = None

try:
    from analyzer.main import AnalyzerWindow
except ImportError:
    AnalyzerWindow = None

# Intentamos importar la ventana de ScreenMaker desde su subcarpeta registrada
try:
    from windows import ScreenMaker
except ImportError:
    ScreenMaker = None


class MainDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Central de Herramientas")
        self.menu_frame = None
        self.mostrar_menu_principal()

    def mostrar_menu_principal(self):
        # Establecemos el tamaño original del panel de control
        self.root.geometry("400x320")
        self.root.resizable(False, False)

        self.menu_frame = tk.Frame(self.root)
        self.menu_frame.pack(fill="both", expand=True)

        tk.Label(self.menu_frame, text="Panel de Control Principal", font=("Segoe UI", 14, "bold")).pack(pady=(20, 5))
        tk.Label(self.menu_frame, text="Selecciona la herramienta que deseas ejecutar:", font=("Segoe UI", 10), fg="#555555").pack(pady=(0, 15))

        btn_analyzer = tk.Button(self.menu_frame, text="🔍   Abrir Analizador", command=self.abrir_analyzer, font=("Segoe UI", 11), width=25, height=1)
        btn_analyzer.pack(pady=5)

        # Botón estilizado para ScreenMaker
        btn_screenmaker = tk.Button(self.menu_frame, text="🛠️   Abrir ScreenMaker", command=self.abrir_screenmaker, font=("Segoe UI", 11), width=25, height=1, bg="#e2f0fe")
        btn_screenmaker.pack(pady=5)

        btn_packer = tk.Button(self.menu_frame, text="📦   Abrir Packer", command=self.abrir_packer, font=("Segoe UI", 11, "bold"), width=25, height=1, bg="#d1e7dd")
        btn_packer.pack(pady=5)

    def abrir_packer(self):
        if PackerWindow:
            self.menu_frame.destroy()
            PackerWindow(self.root, volver_callback=self.mostrar_menu_principal)
        else:
            messagebox.showerror("Error", "No se pudo importar el módulo PackerWindow.")

    def abrir_analyzer(self):
        if AnalyzerWindow is None:
            messagebox.showerror(
                "Error de Importación", 
                "No se pudo cargar AnalyzerWindow al arrancar.\nVerifica que la carpeta se llame 'analyzer' y contenga un 'main.py'."
            )
            return

        try:
            menu_a_eliminar = self.menu_frame
            self.analyzer_app = AnalyzerWindow(self.root, volver_callback=self.mostrar_menu_principal)
            if menu_a_eliminar:
                menu_a_eliminar.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el analizador.\nDetalle: {e}")

    def abrir_screenmaker(self):
        if ScreenMaker is None:
            messagebox.showerror(
                "Error de Importación", 
                "No se pudo cargar ScreenMaker al arrancar.\nVerifica que la subcarpeta 'windowMaker' contenga el archivo 'windows.py'."
            )
            return

        try:
            # Eliminamos el menú actual
            menu_a_eliminar = self.menu_frame
            
            # Inicializamos ScreenMaker pasándole el root y el callback de retorno.
            # Nota: El reajuste de geometría a "680x730" ocurre dentro del __init__ de ScreenMaker automáticamente
            self.screenmaker_app = ScreenMaker(self.root, volver_callback=self.mostrar_menu_principal)
            
            if menu_a_eliminar:
                menu_a_eliminar.destroy()
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir ScreenMaker.\nDetalle: {e}")


if __name__ == "__main__":
    # Arrancamos la aplicación respetando el motor DND si está disponible en la central
    root = TkinterDnD.Tk() if DND_MAIN_AVAILABLE else tk.Tk()
    app = MainDashboard(root)
    root.mainloop()