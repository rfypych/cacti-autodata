import os
import subprocess
import sys
import shutil

def build_executable():
    print("=" * 60)
    print("🚀 MULAI BUILD EXECUTABLE CACTI AUTODATA 🚀")
    print("=" * 60)

    # Try to kill running instances if they exist (to avoid PermissionError)
    print("🔍 Mengecek apakah aplikasi sedang berjalan...")
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "Cacti AutoData Dashboard.exe", "/T"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["taskkill", "/F", "/IM", "Cacti AutoData GUI.exe", "/T"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

    # Clean old builds
    for d in ['build', 'dist']:
        if os.path.exists(d):
            print(f"🧹 Membersihkan folder '{d}' lama...")
            try:
                shutil.rmtree(d)
            except Exception as e:
                print(f"⚠️ Gagal membersihkan '{d}': {e}")
                print("Pastikan aplikasi sudah ditutup dan tidak ada file yang sedang dibuka.")
                if d == 'dist': 
                    sys.exit(1)
            
    # Build Unified Application
    print("\n📦 Menjalankan proses kompilasi Unified Application...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "Cacti AutoData",
        "--noconsole",
        "--onefile",
        "--add-data", f"templates{os.pathsep}templates",
        "--add-data", f"static{os.pathsep}static",
        "--collect-all", "holidays",
        "main.py"  # main.py is the unified entry point
    ]
    
    print("Command:", " ".join(cmd))
    result = subprocess.run(cmd)
    
    # Check results
    if result.returncode == 0 and os.path.exists("dist/Cacti AutoData.exe"):
        print("\n" + "=" * 60)
        print("✅ BUILD SUKSES! Executable tunggal tersedia di folder 'dist'.")
        print("Lokasi: dist/Cacti AutoData.exe")
        print("Keterangan: Berisi Desktop GUI + Web Dashboard")
        print("=" * 60)
    else:
        print("\n❌ Gagal membuild executable.")

if __name__ == "__main__":
    build_executable()
