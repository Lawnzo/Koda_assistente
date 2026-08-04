import os
import sys
import json
from thefuzz import process, fuzz

def get_resource_path(relative_path):
    """Encontra o caminho do arquivo tanto em modo normal quanto no PyInstaller (.exe)."""
    if hasattr(sys, '_MEIPASS'):
        path_meipass = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(path_meipass):
            return path_meipass
    
    # Tenta na raiz do executável/projeto
    path_root = os.path.join(os.getcwd(), relative_path)
    if os.path.exists(path_root):
        return path_root
        
    # Tenta em relação ao diretório do script
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path_base = os.path.join(base_dir, relative_path)
    if os.path.exists(path_base):
        return path_base

    return relative_path

class LocalNLP:
    def __init__(self, intents_file="intents.json", threshold=75):
        self.intents_file = intents_file
        self.threshold = threshold
        self.intents = {}
        self.training_phrases = []
        self.phrase_to_intent = {}
        self.load_intents()

    def load_intents(self):
        full_path = get_resource_path(self.intents_file)
        print(f"[NLP] Carregando intents de: {full_path}")

        if not os.path.exists(full_path):
            print(f"[NLP ERROR] Arquivo {full_path} não encontrado!")
            return

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                self.intents = json.load(f)
            
            self.training_phrases = []
            self.phrase_to_intent = {}

            for intent, phrases in self.intents.items():
                for phrase in phrases:
                    self.training_phrases.append(phrase)
                    self.phrase_to_intent[phrase] = intent
            print(f"[NLP OK] {len(self.training_phrases)} frases treinadas carregadas.")
        except Exception as e:
            print(f"[NLP ERROR] Falha ao ler intents: {e}")

    def classify(self, text):
        text = text.lower().strip()
        if not self.training_phrases:
            return "UNKNOWN", 0

        # Regras diretas de prioridade 100%
        if any(w in text for w in ["hora", "horas", "horário"]):
            return "HORAS", 100
        if any(w in text for w in ["dia", "hoje", "data"]):
            return "DATA", 100
        if any(w in text for w in ["luz", "lâmpada", "iluminação"]):
            return "LUZ", 100
        if any(w in text for w in ["ventilador", "vento", "ventoinha"]):
            return "VENTILADOR", 100

        palavras_visao = ["câmera", "webcam", "dedo", "dedos", "mão", "mãozinha", "segurando", "mostrando", "na minha mão", "tem na mão"]
        if any(w in text for w in palavras_visao) and not any(t in text for t in ["tela", "print"]):
            return "VISAO_WEBCAM", 100

        best_match = process.extractOne(text, self.training_phrases, scorer=fuzz.token_set_ratio)
        if best_match:
            phrase, score = best_match[0], best_match[1]
            if score >= self.threshold:
                intent = self.phrase_to_intent.get(phrase, "UNKNOWN")
                return intent, score

        return "UNKNOWN", 0
