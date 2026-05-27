# ScreenMaker 🛠️ - Android Compose Window Configurator

**ScreenMaker** es una herramienta de interfaz gráfica (GUI) desarrollada en Python con Tkinter. Su objetivo principal es facilitar y automatizar la creación del archivo de configuración `entrada.json`, el cual es utilizado por el motor de generación (`generator.py`) para compilar de forma automática pantallas, componentes (`RadioButtons`, `TextFields`), `ViewModels` y sistemas de rutas en **Jetpack Compose / Kotlin**.

---

## 🚀 ¿Qué problema soluciona?
Evita tener que escribir y formatear a mano estructuras complejas de objetos JSON. Con **ScreenMaker**, puedes diseñar la arquitectura de tus vistas Android Studio de manera visual, reduciendo a cero los errores de sintaxis (comas faltantes, llaves mal cerradas) y permitiéndote compilar el código Kotlin con un solo clic.

---

## 🛠️ Requisitos Previos
* **Python 3.10 o superior** instalado en el sistema.
* Tener el script compilador `generator.py` en la misma carpeta raíz que este proyecto.

---

## 💻 Características y Funcionamiento

La interfaz está dividida en tres secciones estratégicas:

### 1. Configuración Global
* **Package Base:** Define el paquete raíz de tu aplicación Android (por ejemplo, `com.example.pruebas`). Este paquete se inyectará automáticamente en las cabeceras de todos los archivos `.kt` generados.

### 2. Formulario de Creación (Añadir Nueva Pantalla)
* **Nombre Screen:** El identificador de la pantalla en Kotlin (ej: `InsertScreen`, `DetailsScreen`).
* **TextField List:** Lista de campos de texto separados por comas que requerirá la pantalla (ej: `nombre, precio, stock`). El sistema creará un `mutableStateOf` y una función observadora en el ViewModel para cada uno.
* **RadioButton (Opcional):** Permite adjuntar un grupo de selección única definiendo el *Nombre del grupo*, las *Opciones* (separadas por comas) y su *Orientación* (`horizontal` o `vertical`).

### 3. Panel de Acciones Finales (Flujos de Trabajo)
El programa cuenta con cuatro operaciones clave en la parte inferior:

* **🗑️ Limpiar UI:** Vacía por completo la lista actual de pantallas reflejada en la interfaz gráfica.
* **🔍 Previsualizar JSON:** Crea el archivo `entrada.json` y lo abre al instante con el editor de código o texto por defecto de tu sistema operativo para que verifiques su estructura.
* **💻 Generar desde Ventana:** Toma las pantallas diseñadas de manera visual, genera temporalmente el JSON, ejecuta el script `generator.py` para inyectar las carpetas de código en tu proyecto de Android Studio y finalmente **destruye el JSON residual** para mantener tu directorio limpio.
* **📂 Generar desde JSON:** No requiere interactuar con la interfaz gráfica. Si ya tienes un archivo `entrada.json` preexistente y guardado en la carpeta de tu proyecto, este botón lo leerá, compilará las ventanas en Kotlin directamente y **conservará tu JSON intacto** para futuras modificaciones manuales.

---

## 📁 Estructura del Proyecto

Para que el ecosistema funcione correctamente, la arquitectura de archivos debe lucir así:

```text
mi_proyecto_utilidades/
├── main.py            # Hito de entrada que inicializa la app
├── windows.py         # Contiene la interfaz gráfica (ScreenMaker)
├── generator.py       # El script motor que compila el código Kotlin
└── entrada.json       # Archivo de configuración (creado/leído por la app)