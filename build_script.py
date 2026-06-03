import subprocess
import sys
import os

def build_executable():
    print("Iniciando compilación con PyInstaller...")
    
    # Check if pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller no está instalado. Instalándolo ahora...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build command
    # --noconfirm: Overwrite existing build
    # --onefile: Create a single executable
    # --noconsole: Hide the console window on Windows/macOS (GUI only)
    # --name: Name of the executable
    command = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed", # Equivalent to --noconsole
        "--name", "E2E_Extractor",
        "app.py"
    ]
    
    try:
        subprocess.check_call(command)
        print("\n¡Compilación exitosa!")
        print(f"El ejecutable se encuentra en la carpeta 'dist'.")
    except subprocess.CalledProcessError as e:
        print(f"\nError durante la compilación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we run in the directory of the script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_executable()
