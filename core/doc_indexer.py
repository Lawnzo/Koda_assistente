import os
import glob
import time
import threading

class DocumentIndexerThread:
    def __init__(self, vector_db, docs_dir=None):
        self.vector_db = vector_db
        if docs_dir is None:
            docs_dir = os.path.join(os.getcwd(), "memoria_docs")
        
        os.makedirs(docs_dir, exist_ok=True)
        self.docs_dir = docs_dir
        self.indexed_files = set()
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()

    def _watch_loop(self):
        print(f"[DOC INDEXER] Monitorando a pasta '{self.docs_dir}' para indexação automática de documentos...")
        while self.running:
            try:
                patterns = ["*.txt", "*.md", "*.json"]
                for p in patterns:
                    for filepath in glob.glob(os.path.join(self.docs_dir, p)):
                        mtime = os.path.getmtime(filepath)
                        file_key = f"{filepath}_{mtime}"
                        if file_key not in self.indexed_files:
                            print(f"[DOC INDEXER] Novo arquivo detectado: {os.path.basename(filepath)}. Indexando no banco vetorial...")
                            ok, msg = self.vector_db.indexar_arquivo(filepath)
                            if ok:
                                self.indexed_files.add(file_key)
            except Exception as e:
                print(f"[DOC INDEXER ERROR] {e}")

            time.sleep(5) # Verifica a cada 5 segundos

    def stop(self):
        self.running = False
