import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from skills.base_skill import BaseSkill

class GoogleServicesSkill(BaseSkill):
    def __init__(self, config=None, brain=None):
        super().__init__(config)
        self.brain = brain
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']

    def can_handle(self, intent):
        return intent == "EMAIL"

    def execute(self, intent, command_text):
        return self.check_emails()

    def check_emails(self):
        try:
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', self.scopes)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists('credentials.json'):
                        return "Lucas, não encontrei o arquivo de credenciais do Google na pasta.", "GMAIL_ERR"
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.scopes)
                    creds = flow.run_local_server(port=0)

                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(
                userId='me', 
                labelIds=['INBOX', 'UNREAD'], 
                maxResults=3
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                return "A sua caixa de entrada está limpa no momento, sem e-mails novos.", "GMAIL_SYNC"

            dados_emails = []
            for msg in messages:
                txt = service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = txt['payload']['headers']

                remetente = next((d['value'] for d in headers if d['name'] == 'From'), "Desconhecido")
                assunto = next((d['value'] for d in headers if d['name'] == 'Subject'), "Sem Assunto")
                snippet = txt.get('snippet', 'Sem conteúdo')

                nome_remetente = remetente.split('<')[0].strip()
                dados_emails.append(f"De: {nome_remetente} | Assunto: {assunto} | Resumo: {snippet}")

            if self.brain:
                prompt_ia = (
                    "Você é o assistente Koda. Resuma estes e-mails para o Lucas de forma natural e rápida. "
                    "Seja direto e claro. IMPORTANTE: Não use asteriscos, negrito ou listas.\n\n"
                    f"E-mails:\n{dados_emails}"
                )
                resposta = self.brain.ask(prompt_ia)
                texto_final = resposta.replace("*", "").replace("#", "").replace("_", "")
                return texto_final, "GMAIL_AI"
            else:
                return f"Você tem {len(messages)} e-mails novos não lidos.", "GMAIL_SYNC"

        except Exception as e:
            print(f"[GMAIL ERROR] {e}")
            return "Ocorreu um erro ao tentar acessar os seus e-mails.", "GMAIL_ERR"
