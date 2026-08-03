import os
from datetime import datetime
from skills.base_skill import BaseSkill

class DevAssistantSkill(BaseSkill):
    def __init__(self, config=None, brain=None):
        super().__init__(config)
        self.brain = brain
        self.file_path = "SOLICITACOES_DEV.md"

    def can_handle(self, intent):
        return intent == "DEV_TASK"

    def execute(self, intent, command_text):
        cmd_clean = command_text.replace("nova tarefa", "").replace("tarefa de dev", "").replace("para o antigravity", "").replace("anotar funcionalidade", "").replace("implementar", "").strip()

        if len(cmd_clean) < 3:
            return "Não consegui capturar o conteúdo da tarefa para o desenvolvedor.", "DEV_TASK_ERR"

        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Se houver IA disponível, gera um resumo estruturado
        if self.brain:
            prompt = (
                "Você é o assistente Koda. O Lucas ditou uma nova funcionalidade para ser implementada no código pelo IA Antigravity. "
                "Resuma o pedido em formato de tarefa clara de engenharia de software com título e bullet points.\n\n"
                f"Pedido Ditado: {cmd_clean}"
            )
            resumo = self.brain.ask(prompt)
        else:
            resumo = f"### Solicitação Ditada:\n- {cmd_clean}"

        conteudo = f"\n\n## 📝 Solicitação de Desenvolvimento ({agora})\n{resumo}\n"

        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(conteudo)
            
            return "Sua solicitação de desenvolvimento foi registrada com sucesso no arquivo de tarefas.", "DEV_TASK_OK"
        except Exception as e:
            print(f"[DEV SKILL ERROR] {e}")
            return "Ocorreu um erro ao salvar a solicitação no arquivo.", "DEV_TASK_ERR"
