import os
import subprocess
import shutil
import time

def kill_emulator_processes():
    print("[-] Cerrando a la fuerza procesos del emulador y ADB...")
    target_processes = ["qemu-system-x86_64.exe", "adb.exe"]
    for process in target_processes:
        try:
            subprocess.run(["taskkill", "/F", "/T", "/IM", process], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"    [✓] Proceso verificado: {process}")
        except Exception:
            pass
    time.sleep(1)

def clear_emulator_locks():
    print("\n[-] Limpiando archivos de bloqueo (.lock)...")
    home_dir = os.path.expanduser("~")
    avd_dir = os.path.join(home_dir, ".android", "avd")
    
    if not os.path.exists(avd_dir):
        return

    for item in os.listdir(avd_dir):
        item_path = os.path.join(avd_dir, item)
        if item.endswith(".avd") and os.path.isdir(item_path):
            for root, dirs, files in os.walk(item_path):
                for directory in dirs:
                    if directory.endswith(".lock"):
                        try:
                            shutil.rmtree(os.path.join(root, directory))
                            print(f"    [✓] Bloqueo eliminado en {item}")
                        except Exception:
                            pass

def get_android_sdk_path():
    # Intentamos buscar dónde tienes instalado el SDK de Android
    android_home = os.environ.get("ANDROID_HOME")
    if not android_home:
        android_home = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Android", "Sdk")
    return android_home if os.path.exists(android_home) else None

def create_medium_phone(sdk_path):
    print("\n[-] Generando un nuevo 'Medium Phone' limpio...")
    
    avdmanager = os.path.join(sdk_path, "cmdline-tools", "latest", "bin", "avdmanager.bat")
    if not os.path.exists(avdmanager):
        avdmanager = os.path.join(sdk_path, "tools", "bin", "avdmanager.bat")
        
    if not os.path.exists(avdmanager):
        print("    [X] No se encontró 'avdmanager'.")
        return

    avd_name = "Medium_Phone_Limpio"
    
    # CAMBIAMOS ESTA LÍNEA: Usamos la API 36 (Android 16) que tu consola dice que tienes disponible
    target_package = "system-images;android-36;google_apis_playstore;x86_64"
    
    cmd = f'echo no | "{avdmanager}" create avd -n "{avd_name}" -k "{target_package}" -d "medium_phone" --force'
    
    try:
        print(f"    [*] Ejecutando avdmanager para crear '{avd_name}' usando Android 16...")
        resultado = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if resultado.returncode == 0:
            print(f"    [✓] ¡Éxito! El dispositivo '{avd_name}' ha sido creado.")
            print("    [!] Ya puedes abrir Android Studio; lo verás listado en el Device Manager.")
        else:
            print("    [X] No se pudo crear automáticamente.")
            print(f"    Detalle del sistema: {resultado.stderr.strip()}")
    except Exception as e:
        print(f"    [X] Error al ejecutar el comando: {e}")

if __name__ == "__main__":
    print("=============================================")
    print("  REPARADOR Y CREADOR AUTOMÁTICO DE AVD     ")
    print("=============================================\n")
    
    kill_emulator_processes()
    clear_emulator_locks()
    
    sdk = get_android_sdk_path()
    if sdk:
        create_medium_phone(sdk)
    else:
        print("[X] No se pudo localizar la ruta de tu SDK de Android automáticamente.")
        print("[!] Por favor, abre Android Studio y crea el dispositivo desde 'Create Virtual Device'.")
        
    print("\n=============================================")