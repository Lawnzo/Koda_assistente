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
    def __init__(self, config=None, nlp_engine=None, brain=None):
        self.config = config
        self.nlp = nlp_engine if nlp_engine else LocalNLP()
        self.brain = brain
        self.skills = []

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

        # 3. Tenta encontrar uma skill registrada para essa intenção
        if intent != "UNKNOWN":
            for skill in self.skills:
                if skill.can_handle(intent):
                    return skill.execute(intent, cmd)

        # 4. Fallback: Se nenhuma skill local resolver, chama o Gemini Brain
        if self.brain:
            print("[DISPATCHER] Fallback acionado -> Encaminhando para Gemini Brain.")
            prompt = f"Você é o Koda, assistente pessoal do Lucas. Responda de forma curta e natural: {cmd}"
            response_text = self.brain.ask(prompt)
            return response_text, "IA_CHAT"

        return "Não consegui compreender nem executar este comando.", "SYS_ERR"
