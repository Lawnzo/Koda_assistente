# Registro de Mudanças do Assistente Koda (Projeto Jarvis)

Este arquivo documenta todas as alterações arquiteturais e novas funcionalidades implementadas no Koda para transformá-lo em um assistente de inteligência artificial de alto nível.

---

## Versão 2.0: Arquitetura Modular OOP, HUD Néon Transparente, Vozes Neurais & Nó Satélite
**Data:** 03 de Agosto de 2026

### 📝 O que mudou hoje:
- **Arquitetura Orientada a Objetos (Koda 2.0):** Reestruturação total do projeto em classes desacopladas (`core/nlp.py`, `core/tts.py`, `core/brain.py`, `core/dispatcher.py`, `core/wake_word.py`).
- **Interface Visual HUD Neon & Transparência Total:** 
  - HUD em Pygame com 35 partículas de energia orbital, espectro gráfico de áudio em tempo real de 16 barras, radar sweep e transição de cores HSL.
  - Correção técnica de transparência Win32 (`pygame.NOFRAME` sem `DOUBLEBUF` + GDI `SetLayeredWindowAttributes` com `LWA_COLORKEY`), eliminando 100% de caixas e bordas pretas no modo minimizado.
- **Gerenciamento de Vozes Neurais (Jarvis PT-BR & UK):**
  - Integração com vozes neurais da Microsoft (`pt-BR-AntonioNeural` para o Jarvis em Português e `en-GB-RyanNeural` para o Jarvis Britânico).
  - Troca dinâmica de perfil de voz por comando falado através da `VoiceSkill`.
- **Nó de Visão Satélite Wi-Fi (`satelite_cam.py` & `skills/webcam_vision.py`):**
  - Servidor de câmera remoto ultrarrápido rodando com DirectShow (`cv2.CAP_DSHOW`) e captura assíncrona por Threads.
  - Permite que o PC principal (mesmo sem webcam) utilize a câmera de um notebook na mesma rede Wi-Fi para analisar o ambiente via Gemini 2.5 Vision por voz.
- **Auto-Programação & Assistente de Engenharia por Voz (`skills/auto_coder.py` & `skills/dev_assistant.py`):**
  - Ditado de solicitações de código salvas em `SOLICITACOES_DEV.md`.
  - Módulo autônomo interativo de 3 etapas com explicação prévia do plano de código, confirmação do usuário, geração de código Python com comentários em português e reinicialização automática e segura na Thread Principal do Windows.
  - Organização e carregamento automático de habilidades personalizadas na pasta `skills/custom_skills/`.

---

## Versão 1.1: Otimização de Processamento (Arquitetura Local-First)
**Data:** 02 de Agosto de 2026

### 📝 O que mudou:
- **Processamento de Linguagem Natural (NLP) Local:** O núcleo de processamento do Koda foi atualizado. Em vez de acionar o Gemini para cada frase dita pelo usuário, o Koda usa `thefuzz` para entender intenções locais.
- **Extração de Dados (`intents.json`):** A base de conhecimento de comandos do Koda foi movida para um arquivo `intents.json`.
- **Gatilho de Inteligência (Fallback):** O Gemini 2.5 só é acionado se a confiança do NLP local for menor que 70%.
