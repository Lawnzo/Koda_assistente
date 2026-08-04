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
        
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.running = True
        
        # Thread para gerar o áudio paralelamente (Download da API)
        self.gen_thread = threading.Thread(target=self._generation_worker, daemon=True)
        self.gen_thread.start()
        
        # Thread para tocar o áudio (Playback)
        self.play_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.play_thread.start()

    def set_active_voice(self, voice_code):
        if voice_code:
            self.active_voice = voice_code
            print(f"[TTS] Voz ativa alterada para: {voice_code}")

    async def _generate_audio_async(self, text, voice):
        temp_file = f"fala_{int(time.time()*1000)}_{hash(text)}.mp3"
        communicate = edge_tts.Communicate(text, voice, rate="+10%")
        await communicate.save(temp_file)
        return temp_file

    def _generation_worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while self.running:
            try:
                text, voice = self.text_queue.get(timeout=0.2)
                try:
                    temp_file = loop.run_until_complete(self._generate_audio_async(text, voice))
                    self.audio_queue.put(temp_file)
                except Exception as e:
                    print(f"[TTS GEN ERROR] {e}")
                self.text_queue.task_done()
            except queue.Empty:
                continue

    def _playback_worker(self):
        while self.running:
            try:
                temp_file = self.audio_queue.get(timeout=0.2)
                try:
                    pygame.mixer.music.load(temp_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() and self.running:
                        time.sleep(0.01)
                    pygame.mixer.music.unload()
                except Exception as e:
                    print(f"[TTS PLAY ERROR] {e}")
                
                # Cleanup the file after playing
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                        
                self.audio_queue.task_done()
            except queue.Empty:
                continue

    def speak(self, text, voice=None):
        if text:
            target_voice = voice if voice else self.active_voice
            import re
            # Divide o texto em frases para processamento contínuo (Streaming falso)
            frases = re.split(r'(?<=[.!?]) +', text)
            for frase in frases:
                if frase.strip():
                    self.text_queue.put((frase.strip(), target_voice))

    def is_speaking(self):
        return pygame.mixer.music.get_busy() or not self.text_queue.empty() or not self.audio_queue.empty()

    def stop(self):
        self.running = False

    def interrupt(self):
        # Limpa as filas de fala para que as próximas frases não sejam lidas nem geradas
        with self.text_queue.mutex:
            self.text_queue.queue.clear()
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
            
        # Interrompe o áudio atual
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        print("[TTS] Fala interrompida pelo usuário.")
