from skills.base_skill import BaseSkill

class MemoryRAGSkill(BaseSkill):
    def __init__(self, config=None, brain=None, vector_db=None):
        super().__init__(config)
        self.brain = brain
        self.vector_db = vector_db

    def can_handle(self, intent):
        return intent in ["MEMORIA_SALVAR", "MEMORIA_CONSULTAR"]

    def execute(self, intent, command_text):
        if not self.vector_db:
            return "Banco de memória vetorial indisponível no momento.", "MEM_ERR"

        cmd_lower = command_text.lower()

        # 1. Salvar Nota na Memória Vetorial
        if intent == "MEMORIA_SALVAR":
            conteudo = command_text
            for g in ["memorize que", "guarde que", "anote que", "lembre-se de que", "salve na memória"]:
                conteudo = conteudo.lower().replace(g, "").strip()

            if len(conteudo) < 2:
                return "Não entendi o que você gostaria que eu memorizasse.", "MEM_ERR"

            ok, msg = self.vector_db.adicionar_nota(conteudo)
            if ok:
                return f"Memorizado com sucesso: {conteudo}.", "MEM_SAVE_OK"
            else:
                return "Ocorreu um erro ao salvar na memória vetorial.", "MEM_ERR"

        # 2. Consultar Nota / Conhecimento na Memória Vetorial
        elif intent == "MEMORIA_CONSULTAR":
            query = command_text
            for g in ["consulte na sua memória", "o que você sabe sobre", "procure na memória", "qual o valor de"]:
                query = query.lower().replace(g, "").strip()

            contextos = self.vector_db.buscar_contexto(query, n_results=3)

            if not contextos:
                return "Consultei minha memória vetorial mas não encontrei nenhuma informação gravada sobre isso.", "MEM_NOT_FOUND"

            fatos = "\n- ".join(contextos)

            if self.brain:
                prompt = (
                    "Você é o assistente Koda. Responda à pergunta do Lucas usando estritamente os fatos recuperados da sua memória vetorial local.\n"
                    "REGRA: Seja extremamente direto, humano e sucinto (máximo 2 frases). Não use formatação markdown.\n\n"
                    f"Fatos Recuperados da Memória Local:\n- {fatos}\n\n"
                    f"Pergunta do Lucas: {command_text}"
                )
                resposta = self.brain.ask(prompt)
                return resposta, "MEM_SEARCH_OK"
            else:
                return f"Encontrei as seguintes informações na memória: {contextos[0]}", "MEM_SEARCH_OK"

        return "Comando de memória não reconhecido.", "MEM_ERR"
