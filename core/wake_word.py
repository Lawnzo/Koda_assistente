import os
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

class OfflineWakeWord:
    def __init__(self, keywords=None, on_wake_callback=None, sample_rate=16000):
        self.keywords = keywords if keywords else ["koda", "computador", "assistente", "jarvis"]
        self.on_wake_callback = on_wake_callback
        self.sample_rate = sample_rate
        self.audio_queue = queue.Queue()
        self.running = False
        self.recognizer = None
        self.model = None

    def initialize(self):
        try:
            print("[WAKE WORD] Carregando modelo local offline em português (Vosk)...")
            self.model = Model(lang="pt")
            
            grammar = json.dumps(self.keywords + ["[unk]"])
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate, grammar)
            print("[WAKE WORD] Modelo de despertar offline ativado com sucesso!")
            return True
        except Exception as e:
            print(f"[WAKE WORD WARN] Falha ao carregar modelo Vosk: {e}")
            return False

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            pass
        self.audio_queue.put(bytes(indata))

    def obter_dispositivo_entrada(self):
        """Encontra o índice de um microfone de entrada válido no sistema."""
        try:
            default_in = sd.default.device[0]
            if default_in is not None and default_in >= 0:
                dev_info = sd.query_devices(default_in)
                if dev_info.get('max_input_channels', 0) > 0:
                    return default_in

            devices = sd.query_devices()
            for idx, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) > 0:
                    print(f"[WAKE WORD] Selecionado microfone alternativo [{idx}]: {dev.get('name')}")
                    return idx
        except Exception as e:
            print(f"[WAKE WORD WARN] Erro ao buscar dispositivos de som: {e}")
        return None

    def listen_loop(self):
        if not self.model and not self.initialize():
            print("[WAKE WORD ERROR] Não foi possível iniciar escuta offline.")
            return

        self.running = True
        input_dev = self.obter_dispositivo_entrada()

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=4000,
                dtype='int16',
                channels=1,
                device=input_dev,
                callback=self._audio_callback
            ):
                print(f"[WAKE WORD] Escuta offline rodando no dispositivo [{input_dev}]! Palavras-chave: {self.keywords}")
                while self.running:
                    try:
                        data = self.audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    if self.recognizer.AcceptWaveform(data):
                        res = json.loads(self.recognizer.Result())
                        text = res.get("text", "").lower()
                        # Usa verificação com espaços para evitar gatilho em sílabas parciais
                        if any(f" {kw} " in f" {text} " for kw in self.keywords):
                            if self.on_wake_callback:
                                self.on_wake_callback(text)
                    else:
                        partial = json.loads(self.recognizer.PartialResult())
                        partial_text = partial.get("partial", "").lower()
                        if any(f" {kw} " in f" {partial_text} " for kw in self.keywords):
                            if self.on_wake_callback:
                                self.on_wake_callback(partial_text)
                            self.recognizer.Reset()
        except Exception as e:
            print(f"[WAKE WORD ERROR] Erro no loop de áudio offline: {e}")

    def stop(self):
        self.running = False
