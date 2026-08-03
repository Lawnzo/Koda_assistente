import os
import io
import requests
from PIL import Image
from skills.base_skill import BaseSkill

class WebcamVisionSkill(BaseSkill):
    def __init__(self, config=None, brain=None):
        super().__init__(config)
        self.brain = brain

    def can_handle(self, intent):
        return intent == "VISAO_WEBCAM"

    def execute(self, intent, command_text):
        if not self.brain:
            return "Cérebro da IA indisponível para análise de câmera.", "ERRO_VISAO"

        ip_notebook = getattr(self.config, 'NOTEBOOK_CAM_IP', '')
        if not ip_notebook:
            return "IP do notebook não configurado no arquivo config.py.", "ERRO_VISAO"

        stream_url = f"http://{ip_notebook}:8080/frame.jpg"

        try:
            print(f"[WEBCAM SATELLITE] Solicitando foto do notebook em {stream_url}...")
            res = requests.get(stream_url, timeout=4)
            if res.status_code == 200:
                image_bytes = res.content
                image_pil = Image.open(io.BytesIO(image_bytes))

                prompt = (
                    "Você é o assistente Koda. Analise a imagem capturada pela câmera do quarto/mesa. "
                    "Descreva quem ou o que está no ambiente de forma muito natural, humana e direta para o Lucas. "
                    "REGRA: Não use formatação de texto (sem asteriscos, negrito ou listas)."
                )

                resposta = self.brain.analyze_image(image_pil, prompt)
                return resposta, "VISION_WEBCAM"
            else:
                return "Não consegui obter a imagem da câmera do notebook.", "ERRO_VISAO"

        except Exception as e:
            print(f"[WEBCAM SATELLITE ERROR] {e}")
            return "Não foi possível conectar à câmera do notebook. Verifique se o script satelite_cam.py está rodando nele.", "ERRO_VISAO"
