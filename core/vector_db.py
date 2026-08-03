import os
import time
import chromadb
from chromadb.config import Settings

class VectorDBEngine:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.join(os.getcwd(), "data", "koda_vector_db")
        
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir
        
        print(f"[VECTOR DB] Inicializando banco vetorial em {data_dir}...")
        self.client = chromadb.PersistentClient(path=data_dir)
        
        # Coleções do Koda
        self.col_notas = self.client.get_or_create_collection(name="koda_notas")
        self.col_docs = self.client.get_or_create_collection(name="koda_documentos")
        print("[VECTOR DB OK] Coleções koda_notas e koda_documentos prontas.")

    def adicionar_nota(self, texto, categoria="geral"):
        if not texto or len(texto.strip()) < 3:
            return False, "Texto muito curto para memorizar."

        doc_id = f"nota_{int(time.time() * 1000)}"
        metadata = {
            "categoria": categoria,
            "timestamp": int(time.time()),
            "fonte": "comando_voz"
        }

        try:
            self.col_notas.add(
                documents=[texto],
                metadatas=[metadata],
                ids=[doc_id]
            )
            print(f"[VECTOR DB] Nota gravada: '{texto[:40]}...' [ID: {doc_id}]")
            return True, f"Nota gravada com sucesso na memória vetorial."
        except Exception as e:
            print(f"[VECTOR DB ERROR] {e}")
            return False, f"Erro ao gravar nota: {e}"

    def buscar_contexto(self, query_text, n_results=3):
        if not query_text or len(query_text.strip()) < 2:
            return []

        resultados = []
        try:
            # Busca nas notas
            res_notas = self.col_notas.query(query_texts=[query_text], n_results=n_results)
            if res_notas and 'documents' in res_notas and len(res_notas['documents']) > 0:
                for docs in res_notas['documents']:
                    for d in docs:
                        resultados.append(d)

            # Busca nos documentos
            res_docs = self.col_docs.query(query_texts=[query_text], n_results=n_results)
            if res_docs and 'documents' in res_docs and len(res_docs['documents']) > 0:
                for docs in res_docs['documents']:
                    for d in docs:
                        resultados.append(d)

        except Exception as e:
            print(f"[VECTOR DB SEARCH ERROR] {e}")

        # Retorna lista de textos relevantes únicos
        return list(dict.fromkeys(resultados))[:n_results]

    def indexar_arquivo(self, filepath):
        if not os.path.exists(filepath):
            return False, "Arquivo não encontrado."

        try:
            filename = os.path.basename(filepath)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if len(content.strip()) < 5:
                return False, "Arquivo vazio."

            # Chunking simples de 500 caracteres
            chunk_size = 500
            overlap = 50
            chunks = []
            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size].strip()
                if chunk:
                    chunks.append(chunk)

            ids = [f"doc_{filename}_{i}" for i in range(len(chunks))]
            metadatas = [{"filename": filename, "chunk_index": i} for i in range(len(chunks))]

            self.col_docs.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            print(f"[VECTOR DB] Arquivo '{filename}' indexado com {len(chunks)} trechos!")
            return True, f"Arquivo {filename} indexado com sucesso com {len(chunks)} partes."
        except Exception as e:
            print(f"[VECTOR DB INDEX ERROR] {e}")
            return False, f"Erro ao indexar arquivo: {e}"
