import subprocess
import sys
import os

def compilar():
    print("=========================================================")
    print("         INICIANDO COMPILAÇÃO DO KODA AI 2.0.exe          ")
    print("=========================================================")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=Koda_v2",
        "--add-data=intents.json;.",
        "--add-data=koda_icon.png;.",
        "main.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n=========================================================")
        print(" SUCCESS! COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
        print(" O executável Koda_v2.exe está na pasta: dist\\Koda_v2\\")
        print("=========================================================")
    except Exception as e:
        print(f"\n[ERRO NA COMPILAÇÃO] {e}")

if __name__ == "__main__":
    compilar()
