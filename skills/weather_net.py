import requests
from skills.base_skill import BaseSkill

class WeatherNetSkill(BaseSkill):
    def can_handle(self, intent):
        return intent in ["CLIMA", "REDE"]

    def execute(self, intent, command_text):
        if intent == "CLIMA":
            return self.get_weather()
        elif intent == "REDE":
            return self.check_network()
        return None, "UTIL_NET"

    def check_network(self):
        try:
            requests.get("https://www.google.com", timeout=3)
            return "Sistemas de rede operacionais e conectados à internet.", "UTIL_NET"
        except Exception:
            return "Atenção: Estamos sem conexão com a internet no momento.", "UTIL_NET_FAIL"

    def get_weather(self):
        api_key = getattr(self.config, 'API_KEY_CLIMA', None)
        city = "Maceio"
        if not api_key:
            return "Chave de API do clima não configurada.", "UTIL_WEATHER_ERR"

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=pt_br"
            res = requests.get(url, timeout=5).json()
            temp = res['main']['temp']
            desc = res['weather'][0]['description']
            return f"Em {city} faz {temp:.1f} graus no momento, com {desc}.", "UTIL_WEATHER"
        except Exception as e:
            print(f"[WEATHER ERROR] {e}")
            return "Não consegui acessar a previsão do tempo no momento.", "UTIL_WEATHER_ERR"
