import os
import psutil
import pyautogui
import webbrowser
from datetime import datetime
from skills.base_skill import BaseSkill

class SystemOpsSkill(BaseSkill):
    def can_handle(self, intent):
        return intent in ["HORAS", "DATA", "STATUS_SISTEMA", "ABRIR_SISTEMA", "FECHAR_SISTEMA", "PESQUISAR"]

    def execute(self, intent, command_text):
        if intent == "HORAS":
            return datetime.now().strftime("Agora são %H horas e %M minutos."), "UTIL_CLOCK"
        elif intent == "DATA":
            return datetime.now().strftime("Hoje é dia %d/%m/%Y."), "UTIL_DATE"
        elif intent == "STATUS_SISTEMA":
            return f"CPU em {psutil.cpu_percent(interval=1)}%. RAM em {psutil.virtual_memory().percent}%.", "UTIL_STATS"
        elif intent == "PESQUISAR":
            search_query = command_text.replace("pesquisar", "").replace("sobre", "").replace("no google", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={search_query}")
            return f"Exibindo resultados para {search_query}.", "WEB_SEARCH"
        elif intent == "ABRIR_SISTEMA":
            return self.open_target(command_text)
        elif intent == "FECHAR_SISTEMA":
            return self.close_target(command_text)

        return None, "SYS_WAIT"

    def open_target(self, cmd):
        targets = getattr(self.config, 'ALVOS_SISTEMA', {})
        for name, path in targets.items():
            if name in cmd:
                if path.startswith("http"):
                    webbrowser.open(path)
                else:
                    os.startfile(path)
                return f"Iniciando {name}.", "SYS_OPEN"
        return "Não encontrei o programa ou site para abrir.", "SYS_OPEN_ERR"

    def close_target(self, cmd):
        processes = getattr(self.config, 'PROCESSOS_SISTEMA', {})
        for name, proc_list in processes.items():
            if name in cmd:
                for p in psutil.process_iter():
                    try:
                        if p.name().lower() in proc_list:
                            p.kill()
                    except Exception:
                        pass
                return f"Encerrando processos de {name}.", "SYS_CLOSE"

        if "janela" in cmd or "tela" in cmd:
            pyautogui.hotkey('alt', 'f4')
            return "Fechando a janela ativa no sistema.", "SYS_CORE"

        return "Não identifiquei o programa para fechar.", "SYS_WAIT"
