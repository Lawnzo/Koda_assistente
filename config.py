import os
from dotenv import load_dotenv

load_dotenv ()

# --- 1. CHAVES E APIs ---
CHAVE_API_GROK = os.getenv("GROK_API_KEY")
API_KEY_CLIMA = os.getenv("CLIMA_KEY")
NOTEBOOK_CAM_IP = os.getenv("NOTEBOOK_CAM_IP", "192.168.0.11")

# --- 2. GATILHOS E COMANDOS DE VOZ ---
GATILHOS_ATIVACAO = ["computador", "assistente", "comando", "koda"]
COMANDOS_DORMIR = ["dormir", "dispensado", "parar de ouvir", "fechar microfone", "desligar microfone", "modo de espera", "pode descansar"]
COMANDOS_MINIMIZAR = ["minimizar", "modo widget", "flutuar", "modo flutuante", "reduzir", "minimize", "mini"]
COMANDOS_MAXIMIZAR = ["maximizar", "painel", "voltar tela", "tela cheia", "abrir painel", "expandir", "expanda"]
COMANDOS_VOZ = ["mudar voz", "trocar voz", "alterar voz", "mude a voz", "troque a voz", "use a voz", "configurar voz", "opções de voz"]

# Vocabulário de Ação do Sistema (Janelas e Programas)
COMANDOS_ABRIR = ["abrir", "abre", "abra", "iniciar", "inicie", "inicia", "acessar", "acesse", "executar", "execute", "lançar"]
COMANDOS_FECHAR = ["fechar", "fecha", "feche", "encerre", "encerra", "encerrar", "finalizar", "finaliza", "finalize", "saia", "sair", "mata", "matar"]
COMANDOS_MIDIA = ["tocar", "toque", "pausar", "pause", "pausa", "parar música", "próxima", "passar", "avançar", "voltar", "anterior", "mutar", "silenciar", "mudo"]

# Vocabulário de Hardware (Dispositivos Físicos)
COMANDOS_LIGAR = ["acender", "acenda", "acende", "ativar", "liga o"]
COMANDOS_DESLIGAR = ["desligar", "desliga", "desligue", "apagar", "apague", "apaga", "desativar"]

# Vocabulário de Utilitários e IA
COMANDOS_HORAS = ["horas", "horário", "que horas são"]
COMANDOS_DATA = ["dia é hoje", "data de hoje", "que dia"]
COMANDOS_CONEXAO = ["teste de conexão", "status da rede", "internet"]
COMANDOS_CLIMA = ["clima", "tempo em", "previsão", "temperatura"]
COMANDOS_VISAO = ["veja", "olhe", "minha tela", "na tela", "analise", "descreva", "imagem", "visão"]
COMANDOS_EMAIL = ["e-mail", "email", "mensagens", "ler meus emails", "caixa de entrada", "ler emails"]
COMANDOS_SISTEMA = ["status do sistema", "cpu", "memória", "desempenho"]
COMANDOS_PESQUISA = ["pesquisar sobre", "pesquise por", "procurar sobre", "procure por", "buscar por", "pesquisar", "pesquise", "buscar", "busque", "procurar", "procure", "pesquisa"]
# --- 3. ALVOS DO SISTEMA (ABERTURA) ---
ALVOS_SISTEMA = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "navegador": "https://www.google.com",
    "whatsapp": "whatsapp://",
    "spotify": "spotify",
    "discord": "discord",
    "steam": "steam",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "chatgpt": "https://chatgpt.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "netflix": "https://www.netflix.com",
    "tradutor": "https://translate.google.com",
    "calculadora": "calc",
    "bloco de notas": "notepad",
    "arquivos": "explorer",
    "explorador": "explorer",
    "painel de controle": "control",
    "gerenciador de tarefas": "taskmgr"
}

# --- 4. PROCESSOS DO SISTEMA (FECHAMENTO NA MEMÓRIA) ---
PROCESSOS_SISTEMA = {
    "bloco de notas": ["notepad.exe", "notepad"],
    "calculadora": ["calculator.exe", "calc.exe"],
    "spotify": ["spotify.exe"],
    "discord": ["discord.exe"],
    "whatsapp": ["whatsapp.exe"],
    "firefox": ["firefox.exe"],
    "edge": ["msedge.exe"],
    "chrome": ["chrome.exe"],
    "excel": ["excel.exe"],
    "word": ["winword.exe"],
    "navegador": ["firefox.exe", "chrome.exe", "msedge.exe"]
}

# --- 5. CONFIGURAÇÕES DA INTELIGÊNCIA ---
DURACAO_ATENCAO = 10  
LIMITE_MEMORIA = 10   

# --- 6. CONFIGURAÇÕES DE ÁUDIO E VOZES ---
TAXA_AMOSTRAGEM = 44100
VOZES_DISPONIVEIS = {
    "antonio": "pt-BR-AntonioNeural",            # Masculino PT-BR (Jarvis em Português)
    "jarvis": "en-GB-RyanNeural",               # Jarvis Britânico (Estilo Homem de Ferro)
    "francisca": "pt-BR-FranciscaNeural",        # Feminina PT-BR
    "thalita": "pt-BR-ThalitaMultilingualNeural" # Feminina Jovem PT-BR
}

# --- 7. CONFIGURAÇÕES VISUAIS (INTERFACE HD 1280x720) ---
LARGURA = 1280
ALTURA = 720
COR_KODA = (0, 255, 200)       # Turquesa Neon
COR_LINHA = (0, 100, 110)      # Azul petróleo 
COR_FUNDO = (5, 10, 15)        # Azul quase preto
COR_TEXTO = (200, 255, 240)    # Branco azulado 
COR_USER = (180, 180, 180)     # Cinza

# --- 8. AUTOMAÇÃO RESIDENCIAL (SMART LIFE / TUYA) ---
LUZ_IP = "192.168.0.6"
LUZ_ID = "eb2aa6b51832d79f17jsim"
LUZ_KEY = "*AmFm!P+q@eLo7Ss"
LUZ_VERSAO = 3.3

# --- Ventilador (Tomada Inteligente) ---
VENT_IP = "192.168.0.3"
VENT_ID = "eb04e8334f91546df2pbxs"
VENT_KEY = "vo+k6Xjy2#xv>S@e"
VENT_VERSAO = 3.3

COMANDOS_VISAO = ["veja", "olhe", "minha tela", "na tela", "analise", "descreva", "imagem", "visão", "traduza", "o que está escrito"]

# GATILHOS DE COMANDOS DE SISTEMA
COMANDOS_ATUALIZACAO = [
    "salvar as atualizações", 
    "salvar atualização", 
    "enviar para o git",
    "gerar nova versão"
    "pode gerar uma nova versão",
    "atualize o sistema",
    "atualizar o sistema",
    "pode atualizar o sistema",
]