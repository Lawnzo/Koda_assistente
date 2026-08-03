from skills.base_skill import BaseSkill

class VoiceSkill(BaseSkill):
    def __init__(self, config=None, tts_engine=None):
        super().__init__(config)
        self.tts = tts_engine

    def can_handle(self, intent):
        return intent == "VOICE_CONFIG"

    def execute(self, intent, command_text):
        cmd = command_text.lower()
        voices = getattr(self.config, 'VOZES_DISPONIVEIS', {})

        for name, code in voices.items():
            if name in cmd:
                if self.tts:
                    self.tts.set_active_voice(code)
                return f"Perfil de voz alterado para {name.capitalize()}.", "VOICE_CONFIG"

        return "Voz não reconhecida. Opções disponíveis: Humberto, Jarvis, Antônio, Francisca, Thalita, Manuela.", "VOICE_CONFIG_ERR"
