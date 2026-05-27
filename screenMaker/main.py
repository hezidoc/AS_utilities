import tkinter as tk
from windows import ScreenMaker

def iniciar_screenMaker():
    ventana = tk.Tk()
    ventana.title("ScreenMaker - Configurar Ventanas Android Compose")
    ventana.geometry("750x700") # Un pelín más ancho para que quepa el nuevo botón holgadamente
    
    # Le pasamos ventana.destroy como callback para cuando se use este script suelto
    app = ScreenMaker(ventana, volver_callback=ventana.destroy)
    ventana.mainloop()

if __name__ == "__main__":
    iniciar_screenMaker()