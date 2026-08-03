import os
import time
import queue
import asyncio
import threading
import pygame
import edge_tts

class TTSEngine:
    def __init__(self, default_voice="pt-BR-AntonioNeural"):
        self.default_voice = default_voice
        self.active_voice = default_voice
        self.speech_queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()

    def set_active_voice(self, voice_code):
        if voice_code:
            self.active_voice = voice_code
            print(f"[TTS] Voz ativa alterada para: {voice_code}")

    async def _generate_audio_async(self, text, voice):
        temp_file = f"fala_{int(time.time()*1000)}.mp3"
        communicate = edge_tts.Communicate(text, voice, rate="+5%")
        await communicate.save(temp_file)
        return temp_file

    def _process_queue(self):
        while self.running:
            try:
                text, voice = self.speech_queue.get(timeout=0.5)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                temp_file = loop.run_until_complete(self._generate_audio_async(text, voice))

                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.music.unload()

                if os.path.exists(temp_file):
                    os.remove(temp_file)

                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TTS ERROR] Exceção durante síntese de fala: {e}")

    def speak(self, text, voice=None):
        if text:
            target_voice = voice if voice else self.active_voice
            self.speech_queue.put((text, target_voice))

    def is_speaking(self):
        return pygame.mixer.music.get_busy() or not self.speech_queue.empty()

    def stop(self):
        self.running = False
