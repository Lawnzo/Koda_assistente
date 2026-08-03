import os
import re
import time
import unicodedata
from skills.base_skill import BaseSkill

def sanitizar_nome_arquivo(texto_prompt):
    nfkd = unicodedata.normalize('NFKD', texto_prompt)
    texto_sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    nome_limpo = re.sub(r'[^a-z0-9_]', '_', texto_sem_acento.lower())
    nome_limpo = re.sub(r'_+', '_', nome_limpo).strip('_')
    return nome_limpo

class AutoCoderSkill(BaseSkill):
    def __init__(self, config=None, brain=None, dispatcher=None):
        super().__init__(config)
        self.brain = brain
        self.dispatcher = dispatcher
        self.custom_folder = os.path.join("skills", "custom_skills")
        os.makedirs(self.custom_folder, exist_ok=True)
        self.pending_description = ""
        self.pending_filename = ""

    def can_handle(self, intent):
        return intent == "AUTO_CODE"

    def execute(self, intent, command_text):
        cmd_clean = command_text.replace("programe", "").replace("crie uma nova skill", "").replace("implemente o código", "").replace("auto programar", "").replace("crie o código", "").replace("escreva o código", "").strip()

        # Se o usuário disse apenas "auto programar" ou "programe", entra no modo interativo
        if len(cmd_clean) < 3:
            return "Entendido, Lucas. O que você gostaria que eu programasse para você?", "WAIT_AUTO_CODE_PROMPT"

        # Se já veio a especificação completa na mesma frase, planeja primeiro
        return self.plan_code(cmd_clean)

    def plan_code(self, description_text):
        if not self.brain:
            return "Cérebro de IA indisponível para planejamento de código.", "AUTO_CODE_ERR"

        self.pending_description = description_text

        # 1. Solicita um nome curto descritivo do arquivo em português
        prompt_nome = (
            "Resuma a funcionalidade solicitada a seguir em 2 ou 3 palavras em português separadas por underline (formato snake_case).\n"
            "Exemplo: silenciar_som, cotacao_dolar, abrir_calculadora\n"
            "Retorne APENAS o nome em snake_case sem extensão.\n\n"
            f"Pedido: {description_text}"
        )
        raw_name = self.brain.ask(prompt_nome).strip()
        clean_name = sanitizar_nome_arquivo(raw_name)
        if not clean_name or len(clean_name) < 2:
            clean_name = sanitizar_nome_arquivo(description_text[:25])
        if not clean_name:
            clean_name = f"skill_{int(time.time())}"

        self.pending_filename = clean_name

        # 2. Solicita uma explicação curta e amigável em português do plano de implementação
        prompt_plano = (
            "Você é o assistente Koda. Explique em APENAS UMA FRASE curta, direta e amigável para o Lucas o que você vai programar para atender o pedido a seguir.\n"
            "REGRA: Não use formatação markdown nem texto longo.\n\n"
            f"Pedido do Lucas: {description_text}"
        )
        explicacao = self.brain.ask(prompt_plano).strip()

        return f"Entendi. {explicacao} Posso prosseguir com a programação?", "WAIT_CODING_PLAN_CONFIRMATION"

    def generate_pending_code(self):
        if not self.brain or not self.pending_description:
            return "Nenhuma especificação pendente para programação.", "AUTO_CODE_ERR"

        file_path = os.path.join(self.custom_folder, f"{self.pending_filename}.py")

        prompt_codigo = (
            "Você é o módulo autônomo de programação do assistente Koda. "
            "Escreva uma classe Python válida que herda de BaseSkill (from skills.base_skill import BaseSkill).\n"
            "REGRAS OBRIGATÓRIAS:\n"
            "1. A classe deve conter o construtor def __init__(self, config=None): super().__init__(config)\n"
            "2. Todos os comentários no código DEVEM ser escritos em português do Brasil.\n"
            "3. As mensagens de retorno e voz do método execute DEVEM ser em português natural e direto, sem asteriscos ou negrito.\n"
            "4. Implemente os métodos can_handle(self, intent) e execute(self, intent, command_text).\n"
            "Retorne EXCLUSIVAMENTE o código Python puro dentro de um bloco ```python ... ``` sem nenhuma introdução ou explicação.\n\n"
            f"Especificação da Funcionalidade: {self.pending_description}"
        )

        code_response = self.brain.ask(prompt_codigo)
        
        if "```python" in code_response:
            code = code_response.split("```python")[1].split("```")[0].strip()
        elif "```" in code_response:
            code = code_response.split("```")[1].split("```")[0].strip()
        else:
            code = code_response.strip()

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            init_file = os.path.join(self.custom_folder, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write("# Pasta de Habilidades Personalizadas Geradas por Voz\n")

            nome_amigavel = self.pending_filename.replace("_", " ")
            self.pending_description = ""
            return f"Programei a habilidade de {nome_amigavel} e salvei no arquivo {self.pending_filename}.py. Deseja reiniciar o aplicativo agora para ativá-la?", "WAIT_RESTART_CONFIRMATION"
        except Exception as e:
            print(f"[AUTO CODER ERROR] {e}")
            return "Ocorreu um erro ao gravar o código gerado no disco.", "AUTO_CODE_ERR"
