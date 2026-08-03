import os
import pyautogui
from PIL import Image
from skills.base_skill import BaseSkill

class VisionSkill(BaseSkill):
    def __init__(self, config=None, brain=None):
        super().__init__(config)
        self.brain = brain

    def can_handle(self, intent):
        return intent == "ANALISAR_TELA"

    def execute(self, intent, command_text):
        if not self.brain:
            return "Módulo de visão offline: cérebro não inicializado.", "ERRO_VISAO"

        try:
            print("[VISION] Capturando tela...")
            screenshot = pyautogui.screenshot()
            temp_path = "visao_koda_temp.png"
            screenshot.save(temp_path)
            
            image_pil = Image.open(temp_path)

            prompt = (
                 "Analise esta tela de jogo/trabalho e encontre os objetivos "
                "ou textos importantes. Diga ao Lucas o que ele precisa fazer em português natural e direto. "
                "REGRA: Nunca use formatação de texto (sem asteriscos, negrito ou listas)."
            )

            response_text = self.brain.analyze_image(image_pil, prompt)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            return response_text, "VISION_TRANSLATOR"
        except Exception as e:
            print(f"[VISION ERROR] {e}")
            return "Não consegui capturar ou processar a visão da tela.", "ERRO_VISAO"
