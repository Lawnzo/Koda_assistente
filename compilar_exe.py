import subprocess
import sys
import os
import shutil
import time

def limpar_pasta(pasta):
    if os.path.exists(pasta):
        print(f"Limpando {pasta}...")
        try:
            shutil.rmtree(pasta, ignore_errors=True)
        except:
            pass

def compilar():
    print("=========================================================")
    print("       CRIANDO O KODA AI 2.0.exe DO ZERO (CLEAN BUILD)   ")
    print("=========================================================")
    
    try:
        subprocess.run('taskkill /f /im Koda_v2.exe', shell=True, capture_output=True)
        time.sleep(1)
    except:
        pass
    
    # 1. Limpeza rigorosa
    limpar_pasta("build")
    limpar_pasta("dist")
    limpar_pasta("dist_temp")
    limpar_pasta("__pycache__")
    
    for f in os.listdir("."):
        if f.endswith(".spec") or f == "desktop.ini":
            try: os.remove(f)
            except: pass

    # Pasta temporária segura fora do OneDrive
    temp_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "KodaBuild")
    dist_temp = os.path.join(temp_dir, "dist")
    build_dir = os.path.join(temp_dir, "build")
    limpar_pasta(temp_dir)

    print("\n[!] Instalando PyInstaller (caso esteja corrompido)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"], check=False)

    print("\n[!] Iniciando a compilação. Isso pode demorar alguns minutos...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=Koda_v2",
        f"--distpath={dist_temp}",
        f"--workpath={build_dir}",
        "--clean",
        
        # Inclusão forçada de TUDO de bibliotecas dinâmicas para evitar erros "ModuleNotFoundError"
        "--collect-all=chromadb",
        "--collect-all=onnxruntime",
        "--collect-all=tokenizers",
        "--collect-all=tinytuya",
        "--collect-all=vosk",
        "--collect-all=sounddevice",
        "--collect-all=pygame",
        "--collect-all=openai",
        "--collect-all=httpx",
        "--collect-all=cryptography",
        "--collect-all=certifi",
        "--collect-all=googleapiclient",
        "--collect-all=google_auth_oauthlib",
        "--collect-all=dotenv",
        
        # Módulos nativos e de rede do Windows e python
        "--hidden-import=_socket",
        "--hidden-import=socket",
        "--hidden-import=ssl",
        "--hidden-import=sqlite3",
        "--hidden-import=asyncio",

        "--add-data=intents.json;.",
        "--add-data=koda_icon.png;.",
        "main.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        
        # Movimentação segura do CONTEÚDO para a pasta dist
        dist_final = os.path.join(os.getcwd(), "dist")
        if not os.path.exists(dist_final):
            os.makedirs(dist_final)
            
        print(f"\n[!] Movendo os arquivos do executável pronto diretamente para: {dist_final}")
        build_output = os.path.join(dist_temp, "Koda_v2")
        
        for item in os.listdir(build_output):
            s = os.path.join(build_output, item)
            d = os.path.join(dist_final, item)
            if os.path.exists(d):
                if os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
                else:
                    os.remove(d)
            shutil.move(s, d)

        # Copiando arquivos extras
        if os.path.exists(".env"):
            shutil.copy(".env", os.path.join(dist_final, ".env"))

        # Limpeza final
        print("\n[!] Limpando arquivos de construção temporários...")
        limpar_pasta(temp_dir)
        
        print("\n=========================================================")
        print(" SUCCESS! COMPILAÇÃO DO ZERO CONCLUÍDA!")
        print(f" SEU APLICATIVO ESTÁ EM: {os.path.join(destino_final, 'Koda_v2.exe')}")
        print("=========================================================")

    except Exception as e:
        print(f"\n[ERRO FATAL NA COMPILAÇÃO] {e}")

if __name__ == "__main__":
    compilar()
