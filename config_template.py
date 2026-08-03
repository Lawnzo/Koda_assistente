# config_template.py - Exemplo de Arquivo de Configuração do Koda 2.0
import os
from dotenv import load_dotenv

load_dotenv()

# APIs
CHAVE_API_GEMINI = os.getenv("GEMINI_KEY", "SUA_CHAVE_GEMINI_AQUI")
API_KEY_CLIMA = os.getenv("CLIMA_KEY", "SUA_CHAVE_OPENWEATHER_AQUI")

# Gatilhos de Voz
GATILHOS_ATIVACAO = ["koda", "computador", "assistente"]
COMANDOS_MINIMIZAR = ["minimizar", "modo widget"]
COMANDOS_MAXIMIZAR = ["maximizar", "painel"]

# Interface
LARGURA = 800
ALTURA = 600
COR_KODA = (0, 255, 200)
COR_FUNDO = (5, 10, 15)
COR_TEXTO = (200, 255, 240)

# Hardware / Smart Home
LUZ_IP = "192.168.0.10"
LUZ_ID = "SEU_ID_TUYA"
LUZ_KEY = "SUA_KEY_TUYA"
LUZ_VERSAO = 3.3

VENT_IP = "192.168.0.3"
VENT_ID = "SEU_ID_TUYA_VENT"
VENT_KEY = "SUA_KEY_TUYA_VENT"
VENT_VERSAO = 3.3
