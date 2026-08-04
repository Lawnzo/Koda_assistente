import os
import sys
import base64
import re
from io import BytesIO

# Garante certificados SSL do certifi em executáveis PyInstaller congelados
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['CURL_CA_BUNDLE'] = certifi.where()
except Exception:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class GrokBrain:
    def __init__(self, api_key, model_name="llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.preferred_model = model_name
        self.vision_model = "llama-3.2-90b-vision-preview" # Modelo com suporte a visão e melhor compreensão em PT-BR
        self.client = None
        
        if not OpenAI:
            print("[BRAIN WARN] A biblioteca 'openai' não está instalada. Groq indisponível.")
            return

        if api_key and api_key.strip():
            try:
                # Inicializa cliente OpenAI apontando para a Groq API com timeout
                self.client = OpenAI(
                    api_key=api_key.strip(),
                    base_url="https://api.groq.com/openai/v1",
                    timeout=10.0
                )
            except Exception as e:
                print(f"[BRAIN WARN] Falha ao inicializar SDK da OpenAI para Groq: {e}")
        else:
            print("[BRAIN WARN] Chave da API da Groq vazia ou não informada.")

    def test_connection(self):
        if not self.client:
            return "NO API KEY"
        try:
            self.client.chat.completions.create(
                model=self.preferred_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            return "ONLINE"
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower():
                return "ERR: QUOTA EXCEEDED (429)"
            if "401" in err_str or "unauthorized" in err_str.lower():
                return "ERR: INVALID KEY (401)"
            return "OFFLINE / ERROR"

    def ask(self, prompt_text, system_instruction=None):
        if not self.client:
            return "Lucas, meu núcleo de IA não está configurado com uma chave de API válida no arquivo .env."

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        
        messages.append({"role": "user", "content": prompt_text})

        try:
            response = self.client.chat.completions.create(
                model=self.preferred_model,
                messages=messages,
                max_tokens=150
            )
            if response and response.choices:
                raw_text = response.choices[0].message.content
                # Remove blocos de raciocínio <think>...</think> caso um modelo de raciocínio seja usado, mesmo que não seja fechado
                clean_text = re.sub(r'<think>.*?(?:</think>|$)', '', raw_text, flags=re.DOTALL).strip()
                
                if not clean_text:
                    return "Tive um lapso de raciocínio, desculpe."
                    
                return clean_text
        except Exception as e:
            err_str = str(e)
            print(f"[BRAIN ERROR MODEL {self.preferred_model}]: {err_str}")
            if "401" in err_str or "unauthorized" in err_str.lower():
                return "Minha chave de API do Grok foi recusada pela xAI. Por favor, verifique a chave no arquivo .env."
            if "429" in err_str:
                return "O limite de uso da API do Grok foi excedido."

        return "Tive uma falha temporária ao conectar ao meu núcleo de pensamento."

    def analyze_image(self, image_pil, prompt_text):
        if not self.client:
            return "Meu módulo de visão precisa de uma chave de API válida no arquivo .env."

        try:
            # Converter imagem PIL para base64 JPEG
            buffered = BytesIO()
            # Garante que a imagem é RGB antes de salvar como JPEG
            if image_pil.mode != 'RGB':
                image_pil = image_pil.convert('RGB')
            image_pil.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # Força o modelo de visão a ser conciso e responder em português
            prompt_seguro = f"[RESPONDA EM PORTUGUÊS DO BRASIL. SEJA EXTREMAMENTE CURTO E DIRETO.]\n{prompt_text}"
            
            # Formato de mensagem para modelos vision compatíveis com API OpenAI
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_seguro},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                max_tokens=150
            )
            
            if response and response.choices:
                raw_text = response.choices[0].message.content
                # Remove bloco de pensamento fechado ou que foi cortado no meio (até o final da string)
                clean_text = re.sub(r'<think>.*?(?:</think>|$)', '', raw_text, flags=re.DOTALL).strip()
                
                if not clean_text:
                    return "Dei uma olhada, mas tive um problema ao tentar processar a resposta."
                
                return clean_text
        except Exception as e:
            err_str = str(e)
            print(f"[BRAIN VISION ERROR]: {err_str}")
            if "401" in err_str or "unauthorized" in err_str.lower():
                return "Minha chave de API do Grok foi recusada durante a análise de tela. Verifique o arquivo .env."

        return "Não foi possível processar a visão da imagem com a IA."
