import random
from core.nlp import LocalNLP

RESPOSTAS_VARIADAS = {
    "quem é você": [
        "Eu sou o Koda, a interface de inteligência do sistema. Como posso ajudar?",
        "Sou o Koda, assistente virtual operacional.",
        "Koda à sua disposição. Todos os sistemas estão prontos."
    ],
    "quem te criou": [
        "Eu fui desenvolvido e programado pelo Lucas.",
        "Minhas diretrizes e meu código foram criados pelo Lucas."
    ],
    "está aí": [
        "Sempre atento.",
        "Operacional e escutando.",
        "Online e aguardando seus comandos."
    ]
}

class CommandDispatcher:
    def __init__(self, config=None, nlp_engine=None, brain=None, vector_db=None):
        self.config = config
        self.nlp = nlp_engine if nlp_engine else LocalNLP()
        self.brain = brain
        self.vector_db = vector_db
        self.skills = []

    def set_vector_db(self, vector_db):
        self.vector_db = vector_db

    def register_skill(self, skill_instance):
        self.skills.append(skill_instance)

    def dispatch(self, text_command):
        cmd = text_command.lower().strip()

        # 1. Respostas rápidas de personalidade
        for key, responses in RESPOSTAS_VARIADAS.items():
            if key in cmd:
                return random.choice(responses), "IA_CHAT"

        # 2. Classificação de Intenção Local
        intent, score = self.nlp.classify(cmd)
        print(f"[DISPATCHER] Comando: '{cmd}' -> Intenção: {intent} (Confiança: {score}%)")

        # 3. Execução Direta de Skills Locais (Horas, Luz, Câmera, Sistema, etc.)
        if intent != "UNKNOWN":
            for skill in self.skills:
                if skill.can_handle(intent):
                    return skill.execute(intent, cmd)

        # 4. Fallback: Se nenhuma skill local resolver, enriquece com RAG e chama o Groq Brain
        if self.brain:
            print("[DISPATCHER] Fallback acionado -> Encaminhando para Groq Brain.")
            
            prompt_envio = (
                f"Você é o Koda, assistente pessoal do Lucas. "
                f"REGRA ABSOLUTA: NUNCA mencione que você é uma IA, um programa, ou que está em um servidor. "
                f"NUNCA fale sobre limitações de servidor ou inteligência artificial. "
                f"Se não souber algo, apenas diga de forma casual que não entendeu ou peça para repetir. "
                f"Responda em NO MÁXIMO 1 ou 2 frases. Seja extremamente direto, rápido e natural. Pergunta: {cmd}"
            )
            
            if self.vector_db:
                contexto_local = self.vector_db.buscar_contexto(cmd, n_results=2)
                if contexto_local:
                    contexto_str = "\n- ".join(contexto_local)
                    prompt_envio = (
                        f"[MEMÓRIA LOCAL DO KODA:\n- {contexto_str}]\n\n"
                        f"Você é o Koda. Use a memória acima se útil. "
                        f"REGRA ABSOLUTA: NUNCA mencione que você é uma IA ou fale sobre servidores/limitações. "
                        f"Responda em NO MÁXIMO 1 ou 2 frases, seja muito direto. Pergunta: {cmd}"
                    )

            response_text = self.brain.ask(prompt_envio)
            return response_text, "IA_CHAT"

        return "Não consegui compreender nem executar este comando.", "SYS_ERR"
