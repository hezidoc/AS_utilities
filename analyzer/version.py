import os
import re
import subprocess
import sys

def get_android_studio_version():
    system = sys.platform

    # --- 1. WINDOWS ---
    if system == "win32":
        # Intenta buscar en el Registro de Windows primero
        import winreg
        paths_to_check = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Android Studio"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Android Studio"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Android Studio")
        ]
        for hkey, subkey in paths_to_check:
            try:
                with winreg.OpenKey(hkey, subkey) as key:
                    version, _ = winreg.QueryValueEx(key, "Version")
                    return f"Android Studio {version} (vía Registro)"
            except FileNotFoundError:
                continue

        # Si no está en el registro, busca en las rutas por defecto
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        
        possible_dirs = [
            os.path.join(program_files, "Android", "Android Studio"),
            os.path.join(local_app_data, "Android", "Android Studio")
        ]
        
        for d in possible_dirs:
            # Intentar leer desde product-info.json si existe
            product_info = os.path.join(d, "product-info.json")
            if os.path.exists(product_info):
                with open(product_info, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'"version"\s*:\s*"([^"]+)"', content)
                    if match:
                        return f"Android Studio {match.group(1)}"

    # --- 2. MACOS ---
    elif system == "darwin":
        plist_path = "/Applications/Android Studio.app/Contents/Info.plist"
        if os.path.exists(plist_path):
            try:
                # Usa el comando 'defaults' nativo de Mac para leer el plist
                version = subprocess.check_output(
                    ["defaults", "read", plist_path, "CFBundleShortVersionString"],
                    text=True
                ).strip()
                return f"Android Studio {version}"
            except Exception:
                pass

    # --- 3. LINUX ---
    elif system.startswith("linux"):
        # En Linux suele distribuirse en carpetas manuales o via Snap/Flatpak
        # Comprobación de Snap
        try:
            snap_list = subprocess.check_output(["snap", "list", "android-studio"], text=True, stderr=subprocess.DEVNULL)
            lines = snap_list.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) > 1:
                    return f"Android Studio {parts[1]} (Snap)"
        except FileNotFoundError:
            pass

        # Buscar en rutas comunes si se instaló manualmente
        home = os.path.expanduser("~")
        possible_paths = [
            "/opt/android-studio",
            os.path.join(home, "android-studio"),
            os.path.join(home, "Downloads", "android-studio")
        ]
        for path in possible_paths:
            product_info = os.path.join(path, "product-info.json")
            if os.path.exists(product_info):
                with open(product_info, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'"version"\s*:\s*"([^"]+)"', content)
                    if match:
                        return f"Android Studio {match.group(1)} (Ruta: {path})"

    return "Android Studio no detectado o instalado en una ruta personalizada."

if __name__ == "__main__":
    print("Buscando versión de Android Studio...")
    version_info = get_android_studio_version()
    print(f"\nResultado: {version_info}")