import tkinter as tk
import sys
import os

# Aseguramos que el analizador encuentre sus propios módulos locales (utils, windows, etc.)
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

from analyzer.windows import AnalyzerWindow

# Intentar importar el motor de Drag & Drop para cuando se use de forma independiente
try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False


def iniciar_analizador():
    """Permite seguir ejecutando este script de forma totalmente independiente"""
    root_class = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk
    ventana = root_class()
    ventana.title("Analizador de Entorno Android Studio")
    ventana.geometry("650x500")
    
    # Definimos la ruta por defecto a AndroidStudioProjects en el perfil de usuario
    ruta_inicial = os.path.join(os.path.expanduser("~"), "AndroidStudioProjects")
    
    # Si la ruta existe, podemos asegurarnos de pasarla (asumiendo que AnalyzerWindow 
    # acepta un parámetro como `ruta_inicial` o `initial_path`).
    # Si tu clase AnalyzerWindow recibe ese parámetro, se lo pasamos aquí:
    try:
        app = AnalyzerWindow(ventana, volver_callback=ventana.destroy, ruta_inicial=ruta_inicial)
    except TypeError:
        # Por si AnalyzerWindow no acepta el argumento directamente, caemos en la inicialización estándar
        app = AnalyzerWindow(ventana, volver_callback=ventana.destroy)
        # Y si tiene algún método para establecer la ruta, lo llamarías aquí, por ejemplo:
        # if hasattr(app, 'set_path'):
        #     app.set_path(ruta_inicial)

    ventana.mainloop()


if __name__ == "__main__":
    iniciar_analizador()