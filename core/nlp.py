import os
import json
from thefuzz import process, fuzz

class LocalNLP:
    def __init__(self, intents_file="intents.json", threshold=70):
        self.intents_file = intents_file
        self.threshold = threshold
        self.intents = {}
        self.training_phrases = []
        self.phrase_to_intent = {}
        self.load_intents()

    def load_intents(self):
        if not os.path.exists(self.intents_file):
            print(f"[NLP WARN] File {self.intents_file} not found.")
            return

        try:
            with open(self.intents_file, "r", encoding="utf-8") as f:
                self.intents = json.load(f)
            
            self.training_phrases = []
            self.phrase_to_intent = {}

            for intent, phrases in self.intents.items():
                for phrase in phrases:
                    self.training_phrases.append(phrase)
                    self.phrase_to_intent[phrase] = intent
        except Exception as e:
            print(f"[NLP ERROR] Failed to parse intents file: {e}")

    def classify(self, text):
        text = text.lower().strip()
        if not self.training_phrases:
            return "UNKNOWN", 0

        # Regra direta de alta prioridade para Câmera / Visão da Webcam
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
