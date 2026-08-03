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

    def listen_loop(self):
        if not self.model and not self.initialize():
            print("[WAKE WORD ERROR] Não foi possível iniciar escuta offline.")
            return

        self.running = True
        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=4000,
                dtype='int16',
                channels=1,
                callback=self._audio_callback
            ):
                print(f"[WAKE WORD] Escuta offline rodando! Palavras-chave: {self.keywords}")
                while self.running:
                    try:
                        data = self.audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue

                    if self.recognizer.AcceptWaveform(data):
                        res = json.loads(self.recognizer.Result())
                        text = res.get("text", "").lower()
                        if any(kw in text for kw in self.keywords):
                            if self.on_wake_callback:
                                self.on_wake_callback(text)
                    else:
                        partial = json.loads(self.recognizer.PartialResult())
                        partial_text = partial.get("partial", "").lower()
                        if any(kw in partial_text for kw in self.keywords):
                            if self.on_wake_callback:
                                self.on_wake_callback(partial_text)
                            self.recognizer.Reset()
        except Exception as e:
            print(f"[WAKE WORD ERROR] Erro no loop offline: {e}")

    def stop(self):
        self.running = False
