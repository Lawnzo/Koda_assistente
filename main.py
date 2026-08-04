import sys
import os
import time
import glob
import importlib.util
import subprocess
import threading
import traceback

# Logger de emergência para capturar qualquer falha de inicialização
def log_fatal(msg):
    try:
        with open("koda_crash.log", "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

try:
    import numpy as np
    import pygame
    import sounddevice as sd
    import speech_recognition as sr
    import win32gui
    import win32con

    import config

    from core.nlp import LocalNLP
    from core.tts import TTSEngine
    from core.brain import GrokBrain
    from core.dispatcher import CommandDispatcher
    from core.wake_word import OfflineWakeWord
    from core.vector_db import VectorDBEngine
    from core.doc_indexer import DocumentIndexerThread

    from skills.smart_home import SmartHomeSkill
    from skills.system_ops import SystemOpsSkill
    from skills.vision import VisionSkill
    from skills.weather_net import WeatherNetSkill
    from skills.google_services import GoogleServicesSkill
    from skills.voice_skill import VoiceSkill
    from skills.webcam_vision import WebcamVisionSkill
    from skills.dev_assistant import DevAssistantSkill
    from skills.auto_coder import AutoCoderSkill
    from skills.memory_rag import MemoryRAGSkill

    from ui.hud import HudKoda
except Exception as e_import:
    log_fatal(f"ERRO DE IMPORTAÇÃO NO ARRANQUE: {e_import}\n{traceback.format_exc()}")
    sys.exit(1)

# State Variables
audio_visual = np.zeros(1024)
executando = True
processando_comando = False
tempo_modo_atento = 0
solicitou_minimizar = False
solicitou_maximizar = False
solicitou_reiniciar = False
aguardando_especificacao_codigo = False
aguardando_confirmacao_plano = False
aguardando_confirmacao_reiniciar = False
modulo_atual = "SISTEMA_IDLE"
log_eventos = [("SYS.INIT: KODA CORE v2.0 HD ONLINE.", (0, 220, 255))]

# Component Initialization
tts = TTSEngine(default_voice=config.VOZES_DISPONIVEIS.get("antonio", "pt-BR-AntonioNeural"))
brain = GrokBrain(api_key=getattr(config, 'CHAVE_API_GROK', ''))

try:
    from openai import OpenAI
    groq_client = OpenAI(api_key=getattr(config, 'CHAVE_API_GROK', ''), base_url="https://api.groq.com/openai/v1")
except ImportError:
    groq_client = None
nlp = LocalNLP(intents_file="intents.json")
vector_db = VectorDBEngine()
doc_indexer = DocumentIndexerThread(vector_db=vector_db)

auto_coder_skill = AutoCoderSkill(config, brain)
webcam_skill = WebcamVisionSkill(config, brain)

dispatcher = CommandDispatcher(config=config, nlp_engine=nlp, brain=brain, vector_db=vector_db)
dispatcher.register_skill(SmartHomeSkill(config))
dispatcher.register_skill(SystemOpsSkill(config))
dispatcher.register_skill(VisionSkill(config, brain))
dispatcher.register_skill(WeatherNetSkill(config))
dispatcher.register_skill(GoogleServicesSkill(config, brain))
dispatcher.register_skill(VoiceSkill(config, tts))
dispatcher.register_skill(webcam_skill)
dispatcher.register_skill(DevAssistantSkill(config, brain))
dispatcher.register_skill(MemoryRAGSkill(config, brain, vector_db))
dispatcher.register_skill(auto_coder_skill)

def carregar_skills_personalizadas():
    folder = os.path.join("skills", "custom_skills")
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
        return

    pattern = os.path.join(folder, "*.py")
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        if filename.startswith("__"):
            continue

        mod_name = f"custom_skill_{filename[:-3]}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and attr_name != "BaseSkill" and hasattr(attr, "can_handle") and hasattr(attr, "execute"):
                    instance = attr(config)
                    dispatcher.register_skill(instance)
                    log_eventos.append((f"> CUSTOM: {filename} CARREGADA", (0, 255, 150)))
        except Exception as e:
            print(f"[CUSTOM SKILL LOAD ERROR] {filename}: {e}")

carregar_skills_personalizadas()

def ao_despertar_offline(keyword_detectada):
    global tempo_modo_atento, log_eventos, modulo_atual
    
    palavras_interrupcao = ["silêncio", "silencio", "cala a boca", "cala boca", "calaboca", "pare de falar", "fique quieto", "fica quieto", "quieto"]
    if any(p in keyword_detectada for p in palavras_interrupcao):
        tts.interrupt()
        tempo_modo_atento = 0
        modulo_atual = "SISTEMA_IDLE"
        log_eventos.append((f"> WAKE: INTERRUPÇÃO DE FALA ATIVADA", (255, 50, 50)))
        return

    tempo_modo_atento = time.time() + getattr(config, 'DURACAO_ATENCAO', 15)
    log_eventos.append((f"> WAKE: {keyword_detectada.upper()} ATIVADO", (255, 200, 0)))
    modulo_atual = "SISTEMA_ATENTO"

def callback_audio(indata, frames, tempo, status):
    global audio_visual
    audio_visual = indata[:, 0]

def obter_microfone_reconhecimento():
    try:
        mics = sr.Microphone.list_microphone_names()
        for idx, name in enumerate(mics):
            name_lower = name.lower()
            if any(k in name_lower for k in ["microfone", "microphone", "input", "realtek", "array", "headset"]):
                print(f"[AUDIO SR] Usando microfone [{idx}]: {name}")
                return sr.Microphone(device_index=idx)
    except Exception as e:
        print(f"[AUDIO SR WARN] Erro ao buscar lista de microfones: {e}")
    
    try:
        return sr.Microphone()
    except Exception as e:
        print(f"[AUDIO SR ERROR] Microfone padrão indisponível: {e}")
        return None

def escutar_e_processar():
    global processando_comando, tempo_modo_atento, log_eventos, modulo_atual
    global solicitou_minimizar, solicitou_maximizar, solicitou_reiniciar, executando
    global aguardando_especificacao_codigo, aguardando_confirmacao_plano, aguardando_confirmacao_reiniciar

    rec = sr.Recognizer()
    mic = obter_microfone_reconhecimento()

    if mic:
        try:
            with mic as fonte:
                rec.adjust_for_ambient_noise(fonte, duration=1)
            log_eventos.append((f"> AUDIO: MICROFONE CONECTADO OK", (0, 255, 150)))
        except Exception as e:
            log_eventos.append((f"> AUDIO ERR: {str(e)[:30]}", (255, 50, 50)))
    else:
        log_eventos.append((f"> AUDIO ERR: NENHUM MIC DETECTADO", (255, 50, 50)))

    while executando:
        agora = time.time()
        esta_atento = agora < tempo_modo_atento

        if not esta_atento:
            aguardando_especificacao_codigo = False
            aguardando_confirmacao_plano = False
            aguardando_confirmacao_reiniciar = False
            time.sleep(0.1)
            continue

        while tts.is_speaking():
            time.sleep(0.1)

        if not mic:
            time.sleep(1)
            mic = obter_microfone_reconhecimento()
            continue

        try:
            with mic as fonte:
                try:
                    audio = rec.listen(fonte, timeout=1, phrase_time_limit=10)
                except Exception:
                    continue

                try:
                    if groq_client:
                        wav_data = audio.get_wav_data()
                        transcription = groq_client.audio.transcriptions.create(
                            file=("audio.wav", wav_data),
                            model="whisper-large-v3-turbo",
                            language="pt",
                            response_format="text"
                        )
                        texto = transcription.lower().strip()
                    else:
                        texto = rec.recognize_google(audio, language="pt-BR").lower()

                    gatilhos = getattr(config, 'GATILHOS_ATIVACAO', ['koda', 'computador'])
                    
                    for g in gatilhos:
                        texto = texto.replace(g, "")
                        
                    # Filtro de Alucinação do Whisper (Whisper Hallucination)
                    # O modelo Whisper costuma alucinar frases curtas no silêncio
                    texto_limpo = texto.replace(".", "").replace(",", "").replace("!", "").replace("?", "").strip()
                    
                    # Palavras-chave que indicam fortemente uma alucinação
                    fantasmas = [
                        "obrigad", "inscreva", "próxima", "atenção", "servidor de teste",
                        "teste de som", "legendas", "transcrição", "amara", "youtube", 
                        "assista", "silêncio"
                    ]
                    
                    is_alucinacao = False
                    palavras_texto = texto_limpo.split()
                    
                    # Se a frase for curta (até 6 palavras) e tiver um dos fantasmas, bloqueia!
                    if len(palavras_texto) <= 6:
                        for f in fantasmas:
                            if f in texto_limpo:
                                is_alucinacao = True
                                break
                                
                    # Filtro exato para palavras solitárias ou frases muito curtas vazias
                    if texto_limpo in ["teste", "som", "oi", "hum", "amém", "amem", "e aí", "e ai", "umm"]:
                        is_alucinacao = True
                        
                    if is_alucinacao:
                        texto = ""
                    else:
                        texto = texto.strip()

                    if len(texto) >= 1:
                        processando_comando = True
                        log_eventos.append((f"> USR: {texto}", (180, 180, 180)))

                        palavras_negativas = ["não", "nao", "agora não", "cancelar", "espera", "pare"]
                        palavras_afirmativas = ["sim", "pode", "reiniciar", "prosseguir", "gerar", "reinicia", "reinicie", "com certeza", "claro", "bora", "quero", "vá", "vai", "ok", "beleza", "confirmo", "afirmativo", "simples", "por favor", "manda", "pode ser", "uhum"]

                        if aguardando_confirmacao_reiniciar:
                            aguardando_confirmacao_reiniciar = False
                            if not any(n in texto for n in palavras_negativas) and (any(w in texto for w in palavras_afirmativas) or len(texto) < 10):
                                log_eventos.append((f"> SYS: REINICIANDO SISTEMA...", (255, 200, 0)))
                                tts.speak("Reiniciando o aplicativo Koda para carregar a nova habilidade.")
                                solicitou_reiniciar = True
                            else:
                                log_eventos.append((f"> SYS: REINÍCIO CANCELADO", (150, 150, 150)))
                                tts.speak("Entendido. A nova funcionalidade estará ativa na próxima inicialização.")

                        elif aguardando_confirmacao_plano:
                            aguardando_confirmacao_plano = False
                            if not any(n in texto for n in palavras_negativas) and (any(w in texto for w in palavras_afirmativas) or len(texto) < 10):
                                log_eventos.append((f"> SYS: Escrevendo código...", (255, 120, 0)))
                                tts.speak("Certo, estou gerando o código em segundo plano.")
                                resposta, modulo = auto_coder_skill.generate_pending_code()
                                modulo_atual = modulo
                                if modulo == "WAIT_RESTART_CONFIRMATION":
                                    aguardando_confirmacao_reiniciar = True
                                log_eventos.append((f"> SYS: {resposta[:45]}...", (0, 220, 255)))
                                tts.speak(resposta)
                                while tts.is_speaking():
                                    time.sleep(0.1)
                                tempo_modo_atento = time.time() + 15
                            else:
                                log_eventos.append((f"> SYS: PROGRAMAÇÃO CANCELADA", (150, 150, 150)))
                                tts.speak("Entendido, Lucas. Programação cancelada.")

                        elif aguardando_especificacao_codigo:
                            aguardando_especificacao_codigo = False
                            log_eventos.append((f"> SYS: Analisando plano...", (255, 120, 0)))
                            resposta, modulo = auto_coder_skill.plan_code(texto)
                            modulo_atual = modulo
                            if modulo == "WAIT_CODING_PLAN_CONFIRMATION":
                                aguardando_confirmacao_plano = True
                            log_eventos.append((f"> SYS: {resposta[:45]}...", (0, 220, 255)))
                            tts.speak(resposta)
                            while tts.is_speaking():
                                time.sleep(0.1)
                            tempo_modo_atento = time.time() + 15

                        else:
                            intent_pre, _ = nlp.classify(texto)
                            if intent_pre == "CALAR_BOCA":
                                tts.interrupt()
                                tempo_modo_atento = 0
                                modulo_atual = "SISTEMA_IDLE"
                                log_eventos.append((f"> SYS: ÁUDIO E ESCUTA INTERROMPIDOS", (255, 50, 50)))
                                continue

                            cmd_min = getattr(config, 'COMANDOS_MINIMIZAR', ['minimizar'])
                            cmd_max = getattr(config, 'COMANDOS_MAXIMIZAR', ['restaurar', 'maximizar'])

                            if any(c in texto for c in cmd_min):
                                solicitou_minimizar = True
                                modulo_atual = "SYS_UI"
                                tts.speak("Interface minimizada.")
                            elif any(c in texto for c in cmd_max):
                                solicitou_maximizar = True
                                modulo_atual = "SYS_UI"
                                tts.speak("Painel principal restaurado.")
                            else:
                                resposta, modulo = dispatcher.dispatch(texto)

                                modulo_atual = modulo
                                if modulo == "WAIT_AUTO_CODE_PROMPT":
                                    aguardando_especificacao_codigo = True
                                    log_eventos.append((f"> SYS: {resposta[:45]}...", (255, 200, 0)))
                                    tts.speak(resposta)
                                    while tts.is_speaking():
                                        time.sleep(0.1)
                                    tempo_modo_atento = time.time() + 15
                                elif modulo == "WAIT_CODING_PLAN_CONFIRMATION":
                                    aguardando_confirmacao_plano = True
                                    log_eventos.append((f"> SYS: {resposta[:45]}...", (255, 200, 0)))
                                    tts.speak(resposta)
                                    while tts.is_speaking():
                                        time.sleep(0.1)
                                    tempo_modo_atento = time.time() + 15
                                elif modulo == "WAIT_RESTART_CONFIRMATION":
                                    aguardando_confirmacao_reiniciar = True
                                    log_eventos.append((f"> SYS: {resposta[:45]}...", (255, 200, 0)))
                                    tts.speak(resposta)
                                    while tts.is_speaking():
                                        time.sleep(0.1)
                                    tempo_modo_atento = time.time() + 15
                                elif resposta:
                                    log_eventos.append((f"> SYS: {resposta[:45]}...", (0, 220, 255)))
                                    tts.speak(resposta)

                        tempo_modo_atento = time.time() + 15

                except Exception:
                    pass

        except Exception as err_mic:
            log_eventos.append((f"> MIC ERR: {str(err_mic)[:30]}", (255, 50, 50)))
            time.sleep(1)
        finally:
            processando_comando = False

# Main Execution Loop
if __name__ == "__main__":
    try:
        hud = HudKoda(config)
        webcam_skill.set_hud(hud)
        
        def test_grok_connection():
            hud.grok_status = "TESTING..."
            status = brain.test_connection()
            hud.grok_status = status
            log_eventos.append((f"> SYS: GROQ API CHECK -> {status}", (255, 200, 0) if "ERR" in status else (0, 255, 150)))
            
        threading.Thread(target=test_grok_connection, daemon=True).start()

        gatilhos_locais = getattr(config, 'GATILHOS_ATIVACAO', ['koda', 'computador'])
        # Adiciona palavras de interrupção e suas variações comuns para a engine offline
        gatilhos_locais.extend(["silêncio", "silencio", "cala a boca", "cala boca", "calaboca", "pare de falar", "fique quieto", "fica quieto", "quieto"])
        
        wake_engine = OfflineWakeWord(keywords=gatilhos_locais, on_wake_callback=ao_despertar_offline)
        threading.Thread(target=wake_engine.listen_loop, daemon=True).start()

        threading.Thread(target=escutar_e_processar, daemon=True).start()
        
        try:
            dev_in = wake_engine.obter_dispositivo_entrada()
            stream = sd.InputStream(callback=callback_audio, channels=1, samplerate=getattr(config, 'TAXA_AMOSTRAGEM', 44100), device=dev_in)
            stream.start()
        except Exception as e:
            print(f"[AUDIO WARN] Microfone visual não inicializado: {e}")
            stream = None

        clock = pygame.time.Clock()

        while executando:
            if solicitou_minimizar:
                hud.alternar_modo(True)
                solicitou_minimizar = False
            if solicitou_maximizar:
                hud.alternar_modo(False)
                solicitou_maximizar = False

            if solicitou_reiniciar:
                while tts.is_speaking():
                    time.sleep(0.1)
                time.sleep(0.5)
                if stream:
                    stream.stop()
                wake_engine.stop()
                doc_indexer.stop()
                tts.stop()
                hud.fechar()
                
                subprocess.Popen([sys.executable, "main.py"], cwd=os.getcwd())
                os._exit(0)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    executando = False

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and hud.modo_widget:
                    hwnd = pygame.display.get_wm_info()["window"]
                    win32gui.ReleaseCapture()
                    win32gui.SendMessage(hwnd, win32con.WM_NCLBUTTONDOWN, win32con.HTCAPTION, 0)

            agora = time.time()
            atento = agora < tempo_modo_atento

            if tts.is_speaking():
                cor = (0, 220, 255)
                status = "COMUNICAÇÃO ATIVA"
            elif processando_comando:
                cor = (255, 120, 0)
                status = "PROCESSANDO DADOS"
            elif atento:
                cor = (255, 200, 0)
                status = "SISTEMA ATENTO"
            else:
                cor = (0, 220, 255)
                status = "SISTEMA ONLINE"

            hud.desenhar(audio_visual, cor, status, log_eventos, modulo_atual)
            clock.tick(60)

        if stream:
            stream.stop()
        wake_engine.stop()
        doc_indexer.stop()
        tts.stop()
        hud.fechar()

    except Exception as e_fatal:
        log_fatal(f"FALHA FATAL DURANTE A EXECUÇÃO DO MAIN: {e_fatal}\n{traceback.format_exc()}")
        sys.exit(1)
