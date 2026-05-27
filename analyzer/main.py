import tkinter as tk
import sys
import os

# Aseguramos que el analizador encuentre sus propios módulos locales (utils, windows, etc.)
# tanto si se ejecuta desde la raíz como si se ejecuta suelto.
directorio_actual = os.path.dirname(os.path.abspath(__file__))
if directorio_actual not in sys.path:
    sys.path.insert(0, directorio_actual)

# Ahora la importación es segura y absoluta para evitar colisiones
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
    ventana.geometry("650x500") # Pon aquí el tamaño por defecto que use tu analizador
    
    # Arrancamos la UI pasándole la ventana base. 
    # Al usarlo suelto, el callback simplemente cierra la app.
    app = AnalyzerWindow(ventana, volver_callback=ventana.destroy)
    ventana.mainloop()


if __name__ == "__main__":
    iniciar_analizador()