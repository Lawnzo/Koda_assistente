class BaseSkill:
    def __init__(self, config=None):
        self.config = config

    def can_handle(self, intent):
        """Retorna True se esta skill souber tratar a intenção informada."""
        return False

    def execute(self, intent, command_text):
        """Executa a habilidade e retorna uma tupla (resposta_texto, codigo_modulo)."""
        raise NotImplementedError("Skills devem implementar o método execute()")
