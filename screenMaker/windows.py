import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os
import sys

class ScreenMaker:
    def __init__(self, master, volver_callback=None):
        self.root = master
        self.volver_callback = volver_callback
        self.screens_list = []  # Almacén temporal de las pantallas creadas
        self.root.resizable(True, True)

        # Ajustamos el tamaño de la ventana contenedora idéntico al que necesita el formulario
        self.root.geometry("680x730")
        
        # --- FRAME PRINCIPAL COPIADO DE PACKERWINDOW ---
        # Envuelve todo para poder destruirlo limpiamente al salir
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # Botón para regresar al menú principal (solo si venimos desde el main)
        if self.volver_callback:
            tk.Button(
                self.main_frame, 
                text="⬅ Volver al Menú", 
                command=self.regresar,
                font=("Segoe UI", 9)
            ).pack(anchor="w", padx=15, pady=(10, 5))

        # Contenedor interno con scroll o padding para el formulario real
        # Usamos un padding interno cómodo para que no quede pegado a los bordes
        form_container = ttk.Frame(self.main_frame, padding="15")
        form_container.pack(fill=tk.BOTH, expand=True)

        # --- SECCIÓN 1: CONFIGURACIÓN GLOBAL ---
        lbl_global = ttk.Label(form_container, text="Configuración Global", font=("Arial", 11, "bold"))
        lbl_global.pack(anchor=tk.W, pady=(0, 5))

        frame_global = ttk.LabelFrame(form_container, text=" Parámetros Base ", padding="10")
        frame_global.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(frame_global, text="Package Base:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_package = ttk.Entry(frame_global, width=45)
        self.entry_package.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        self.entry_package.insert(0, "com.example.pruebas")

        # --- SECCIÓN 2: FORMULARIO PARA AÑADIR PANTALLA ---
        lbl_screen = ttk.Label(form_container, text="Añadir Nueva Pantalla", font=("Arial", 11, "bold"))
        lbl_screen.pack(anchor=tk.W)

        frame_screen = ttk.LabelFrame(form_container, text=" Datos de la Screen ", padding="10")
        frame_screen.pack(fill=tk.X, pady=(5, 15))

        # Nombre de la pantalla
        ttk.Label(frame_screen, text="Nombre Screen:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_screen_name = ttk.Entry(frame_screen, width=35)
        self.entry_screen_name.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        ttk.Label(frame_screen, text="(Ej: InsertScreen, DeleteScreen)", font=("Arial", 8, "italic")).grid(row=0, column=2, sticky=tk.W)

        # TextFields (separados por comas)
        ttk.Label(frame_screen, text="TextField List:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_fields = ttk.Entry(frame_screen, width=35)
        self.entry_fields.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        ttk.Label(frame_screen, text="(Separados por comas. Ej: nombre,precio)", font=("Arial", 8, "italic")).grid(row=1, column=2, sticky=tk.W)

        # --- SUB-SECCIÓN: RADIO BUTTON (OPCIONAL) ---
        frame_rb = ttk.LabelFrame(frame_screen, text=" RadioButton (Opcional) ", padding="8")
        frame_rb.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)

        ttk.Label(frame_rb, text="Nombre Grupo:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_rb_name = ttk.Entry(frame_rb, width=20)
        self.entry_rb_name.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(frame_rb, text="Opciones:").grid(row=0, column=2, sticky=tk.W, padx=(15, 0), pady=2)
        self.entry_rb_options = ttk.Entry(frame_rb, width=25)
        self.entry_rb_options.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        ttk.Label(frame_rb, text="(Ej: Si,No)", font=("Arial", 8, "italic")).grid(row=0, column=4, sticky=tk.W, padx=5)

        ttk.Label(frame_rb, text="Orientación:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.combo_rb_orientacion = ttk.Combobox(frame_rb, values=["horizontal", "vertical"], width=12, state="readonly")
        self.combo_rb_orientacion.current(0)
        self.combo_rb_orientacion.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Botón para registrar la pantalla en memoria
        self.btn_add_screen = ttk.Button(frame_screen, text="➕ Añadir Pantalla a la Lista", command=self.agregar_pantalla)
        self.btn_add_screen.grid(row=3, column=0, columnspan=3, pady=5)

        # --- SECCIÓN 3: COMPOSICIÓN ACTUAL DEL JSON (LISTBOX) ---
        ttk.Label(form_container, text="Pantallas en el JSON actual:", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        self.listbox_screens = tk.Listbox(form_container, height=6, font=("Courier", 9))
        self.listbox_screens.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- BOTONERA DE ACCIONES FINALES ---
        frame_acciones = ttk.Frame(form_container)
        frame_acciones.pack(fill=tk.X, pady=(10, 0))

        # Izquierda: Limpiar
        self.btn_limpiar = ttk.Button(frame_acciones, text="🗑️ Limpiar UI", command=self.limpiar_todo)
        self.btn_limpiar.pack(side=tk.LEFT, padx=5)

        # Centro-Izquierda: Previsualizar
        self.btn_preview = ttk.Button(frame_acciones, text="🔍 Previsualizar JSON", command=self.previsualizar_json)
        self.btn_preview.pack(side=tk.LEFT, padx=5)

        # Centro-Derecha: Generar desde JSON Físico
        self.btn_generar_json = ttk.Button(frame_acciones, text="📂 Generar desde JSON", command=self.generar_desde_json)
        self.btn_generar_json.pack(side=tk.RIGHT, padx=5)

        # Derecha: Generar desde Interfaz Visual
        self.btn_generar_ui = ttk.Button(frame_acciones, text="💻 Generar desde Ventana", command=self.generar_desde_ventana)
        self.btn_generar_ui.pack(side=tk.RIGHT, padx=5)

    def regresar(self):
        """Destruye el frame de esta ventana y ejecuta el callback de regreso"""
        if self.volver_callback:
            self.main_frame.destroy()
            self.volver_callback()

    def agregar_pantalla(self):
        name = self.entry_screen_name.get().strip()
        if not name:
            messagebox.showerror("Error", "El nombre de la Screen es obligatorio.")
            return

        fields_raw = self.entry_fields.get().strip()
        text_fields = [f.strip() for f in fields_raw.split(",") if f.strip()] if fields_raw else []

        screen_data = {
            "name": name,
            "TextFieldList": text_fields,
            "RadioButton": {}
        }

        rb_name = self.entry_rb_name.get().strip()
        rb_options_raw = self.entry_rb_options.get().strip()

        if rb_name and rb_options_raw:
            rb_options = [o.strip() for o in rb_options_raw.split(",") if o.strip()]
            screen_data["RadioButton"] = {
                "name": rb_name,
                "orientacion": self.combo_rb_orientacion.get(),
                "options": rb_options
            }
        elif rb_name or rb_options_raw:
            messagebox.showwarning("Aviso", "El RadioButton requiere tanto el 'Nombre Grupo' como las 'Opciones'. No se adjuntará.")

        self.screens_list.append(screen_data)
        
        rb_info = f"RB: {rb_name}" if screen_data["RadioButton"] else "Sin RB"
        self.listbox_screens.insert(tk.END, f"• {name:<16} -> TFs: {text_fields} | {rb_info}")

        # Limpiar formulario
        self.entry_screen_name.delete(0, tk.END)
        self.entry_fields.delete(0, tk.END)
        self.entry_rb_name.delete(0, tk.END)
        self.entry_rb_options.delete(0, tk.END)
        self.combo_rb_orientacion.current(0)

    def construir_objeto_json(self):
        package = self.entry_package.get().strip()
        if not package:
            messagebox.showerror("Error", "El campo Package Base es obligatorio.")
            return None
        if not self.screens_list:
            messagebox.showerror("Error", "Por favor, añade al menos una pantalla a la lista.")
            return None
        return {
            "package": package,
            "screens": self.screens_list
        }

    def previsualizar_json(self):
        json_data = self.construir_objeto_json()
        if not json_data:
            return
        try:
            with open("entrada.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            os.startfile("entrada.json")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la previsualización:\n{str(e)}")

    def generar_desde_ventana(self):
        json_data = self.construir_objeto_json()
        if not json_data:
            return
        try:
            sys.path.append(os.getcwd())
            from generator import generar_proyecto

            with open("entrada.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)

            generar_proyecto()

            if os.path.exists("entrada.json"):
                os.remove("entrada.json")

            messagebox.showinfo("Éxito", "¡Ventanas generadas desde la UI! 'entrada.json' eliminado.")
            self.screens_list.clear()
            self.listbox_screens.delete(0, tk.END)
        except ImportError:
            messagebox.showerror("Error de Entorno", "No se localizó 'generator.py'.")
        except Exception as e:
            messagebox.showerror("Error", f"Falló internamente:\n{str(e)}")

    def generar_desde_json(self):
        if not os.path.exists("entrada.json"):
            messagebox.showerror("Error", "No se encontró ningún archivo 'entrada.json' en la carpeta.")
            return
        try:
            sys.path.append(os.getcwd())
            from generator import generar_proyecto
            generar_proyecto()
            messagebox.showinfo("Éxito", "¡Código generado con el archivo 'entrada.json' existente!")
        except ImportError:
            messagebox.showerror("Error de Entorno", "No se localizó 'generator.py'.")
        except Exception as e:
            messagebox.showerror("Error", f"Falló internamente:\n{str(e)}")

    def limpiar_todo(self):
        if messagebox.askyesno("Confirmar", "¿Deseas vaciar la lista por completo?"):
            self.screens_list.clear()
            self.listbox_screens.delete(0, tk.END)