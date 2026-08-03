import subprocess
import sys
import os
import shutil

def compilar():
    print("=========================================================")
    print("         INICIANDO COMPILAÇÃO DO KODA AI 2.0.exe          ")
    print("=========================================================")
    
    # Mata processos anteriores se existirem
    try:
        subprocess.run('taskkill /f /im Koda_v2.exe', shell=True, capture_output=True)
    except Exception:
        pass

    # Garante que a pasta de destino esteja limpa
    dist_dir = os.path.join(os.getcwd(), "dist_koda")
    build_dir = os.path.join(os.getcwd(), "build_koda")
    
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir, ignore_errors=True)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=Koda_v2",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        "--collect-all=vosk",
        "--collect-all=chromadb",
        "--collect-all=onnxruntime",
        "--collect-all=thefuzz",
        "--collect-all=sounddevice",
        "--add-data=intents.json;.",
        "--add-data=koda_icon.png;.",
        "main.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n=========================================================")
        print(" SUCCESS! COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f" O executável Koda_v2.exe está na pasta: {dist_dir}\\Koda_v2\\")
        print("=========================================================")
    except Exception as e:
        print(f"\n[ERRO NA COMPILAÇÃO] {e}")

if __name__ == "__main__":
    compilar()
