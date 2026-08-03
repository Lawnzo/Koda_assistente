import os
import io
import requests
from PIL import Image
from skills.base_skill import BaseSkill

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

class WebcamVisionSkill(BaseSkill):
    def __init__(self, config=None, brain=None, hud=None):
        super().__init__(config)
        self.brain = brain
        self.hud = hud

    def set_hud(self, hud):
        self.hud = hud

    def can_handle(self, intent):
        return intent == "VISAO_WEBCAM"

    def capturar_frame_local(self):
        """Tenta capturar um frame da webcam USB/integrada conectada localmente ao PC/Notebook."""
        if not HAS_OPENCV:
            return None
            
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                return None
            
            # Aquecimento rápido do sensor (2 frames)
            cap.read()
            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                # Converte BGR (OpenCV) para JPEG
                ret_jpg, buffer = cv2.imencode('.jpg', frame)
                if ret_jpg:
                    print("[VISION HYBRID] Frame capturado com SUCESSO da webcam LOCAL!")
                    return buffer.tobytes()
        except Exception as e:
            print(f"[VISION LOCAL WARN] Câmera local não capturada: {e}")
        return None

    def capturar_frame_satelite(self):
        """Tenta capturar um frame do servidor Wi-Fi do notebook (satelite_cam.py)."""
        ip_notebook = getattr(self.config, 'NOTEBOOK_CAM_IP', '')
        if not ip_notebook:
            return None

        stream_url = f"http://{ip_notebook}:8080/frame.jpg"
        try:
            print(f"[VISION HYBRID] Tentando câmera satélite Wi-Fi em {stream_url}...")
            res = requests.get(stream_url, timeout=3)
            if res.status_code == 200:
                print("[VISION HYBRID] Frame capturado com SUCESSO da câmera SATÉLITE Wi-Fi!")
                return res.content
        except Exception as e:
            print(f"[VISION SATELITE WARN] Câmera satélite Wi-Fi offline: {e}")
        return None

    def execute(self, intent, command_text):
        if not self.brain:
            return "Cérebro da IA indisponível para análise de câmera.", "ERRO_VISAO"

        # 1. Tenta captura Local primeiro (Webcam USB ou integrada no notebook)
        image_bytes = self.capturar_frame_local()

        # 2. Se não houver câmera local, tenta a Câmera Satélite Wi-Fi do Notebook
        if not image_bytes:
            image_bytes = self.capturar_frame_satelite()

        # 3. Se nenhuma câmera for encontrada
        if not image_bytes:
            return "Não encontrei nenhuma webcam local nem sinal da câmera satélite no notebook.", "ERRO_VISAO"

        try:
            image_pil = Image.open(io.BytesIO(image_bytes))

            # Atualiza o preview no HUD HD
            if self.hud:
                self.hud.atualizar_preview_camera(image_bytes)

            cmd_lower = command_text.lower()
            
            # Se o usuário pediu explicitamente para descrever todo o ambiente
            if any(w in cmd_lower for w in ["descreva o ambiente", "descreva o quarto", "o que tem no quarto", "descreva o local", "descreva tudo"]):
                prompt = (
                    "Você é o assistente Koda. Descreva o ambiente capturado pela câmera do quarto/mesa de forma natural, humana e direta para o Lucas.\n"
                    "REGRA: Não use formatação de texto (sem asteriscos, negrito ou listas)."
                )
            # Pergunta específica sobre a imagem (ex: quantos dedos, cor da camisa, objeto segurado)
            else:
                prompt = (
                    "Você é o assistente Koda. Responda APENAS e EXATAMENTE o que o Lucas perguntou ao olhar para a imagem da câmera.\n"
                    "REGRA DE OURO: Seja extremamente preciso, direto e conciso (responda em apenas uma frase curta). "
                    "NÃO descreva o ambiente nem outros objetos da cena, a menos que ele tenha pedido isso.\n"
                    "Não use formatação de texto (sem asteriscos, negrito ou listas).\n\n"
                    f"Pergunta do Lucas: {command_text}"
                )

            resposta = self.brain.analyze_image(image_pil, prompt)
            return resposta, "VISION_WEBCAM"

        except Exception as e:
            print(f"[WEBCAM HYBRID ERROR] {e}")
            return "Ocorreu um erro ao processar a imagem da câmera.", "ERRO_VISAO"
