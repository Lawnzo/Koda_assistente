from google import genai

class GeminiBrain:
    def __init__(self, api_key, model_name="gemini-2.5-flash"):
        self.api_key = api_key
        self.preferred_model = model_name
        self.fallback_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        self.client = None
        
        if api_key and api_key.strip():
            try:
                self.client = genai.Client(api_key=api_key.strip())
            except Exception as e:
                print(f"[BRAIN WARN] Falha ao inicializar SDK do GenAI: {e}")
        else:
            print("[BRAIN WARN] Chave da API do Gemini vazia ou não informada.")

    def ask(self, prompt_text, system_instruction=None):
        if not self.client:
            return "Lucas, meu núcleo de IA não está configurado com uma chave de API válida no arquivo .env."

        full_prompt = prompt_text
        if system_instruction:
            full_prompt = f"{system_instruction}\n\nPergunta do Usuário: {prompt_text}"

        # Tenta modelos na ordem de preferência
        models_to_try = [self.preferred_model] + [m for m in self.fallback_models if m != self.preferred_model]

        for model in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=full_prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_str = str(e)
                if "401" in err_str or "UNAUTHENTICATED" in err_str or "ACCESS_TOKEN_TYPE_UNSUPPORTED" in err_str:
                    print(f"[ERRO CRÍTICO GEMINI] Autenticação Recusada (401). Sua chave de API no arquivo .env é inválida ou expirou.")
                    print(f"[DICA] Obtenha uma chave gratuita válida no Google AI Studio: https://aistudio.google.com/")
                    return "Minha chave de API do Gemini foi recusada pelo Google. Por favor, atualize a chave no arquivo .env."
                
                print(f"[BRAIN WARN] Modelo {model} falhou ({e}). Tentando próximo modelo...")

        return "Tive uma falha temporária ao conectar ao meu núcleo de pensamento."

    def analyze_image(self, image_pil, prompt_text):
        if not self.client:
            return "Meu módulo de visão precisa de uma chave de API válida no arquivo .env."

        models_to_try = [self.preferred_model] + [m for m in self.fallback_models if m != self.preferred_model]

        for model in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=[prompt_text, image_pil]
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_str = str(e)
                if "401" in err_str or "UNAUTHENTICATED" in err_str:
                    return "Minha chave de API do Gemini foi recusada durante a análise de tela. Verifique o arquivo .env."
                print(f"[BRAIN VISION WARN] Modelo {model} falhou. Tentando próximo...")

        return "Não foi possível processar a visão da tela com a IA."
