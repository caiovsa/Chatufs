import os
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions

class RAGSystem:
    def __init__(self, documents_dir="documents", db_path="chroma_db"):
        self.documents_dir = documents_dir
        self.db_path = db_path
        
        # Configurar API Key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no .env")
        genai.configure(api_key=api_key)
        
        # Inicializar ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Usar função de embedding customizada do Google
        self.embedding_fn = self._create_embedding_fn(api_key)
        
        # Criar ou obter coleção
        self.collection = self.client.get_or_create_collection(
            name="documents_collection",
            embedding_function=self.embedding_fn
        )

    def _create_embedding_fn(self, api_key):
        # Wrapper simples para compatibilidade com ChromaDB
        class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
            def __call__(self, input: list[str]) -> list[list[float]]:
                # Modelo de embedding do Google
                model = 'models/text-embedding-004' 
                embeddings = []
                for text in input:
                    result = genai.embed_content(
                        model=model,
                        content=text,
                        task_type="retrieval_document"
                    )
                    embeddings.append(result['embedding'])
                return embeddings
        return GeminiEmbeddingFunction()

    def load_documents(self):
        """Lê arquivos da pasta documents e indexa no ChromaDB"""
        print("Carregando documentos...")
        count = 0
        ids = []
        documents = []
        metadatas = []

        if not os.path.exists(self.documents_dir):
            os.makedirs(self.documents_dir)
            print(f"Pasta {self.documents_dir} criada.")
            return

        for filename in os.listdir(self.documents_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.documents_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Chunking simplificado (divisão por parágrafos ou tamanho fixo seria ideal para textos grandes)
                # Aqui vamos dividir por quebras de linha duplas para simplificar
                chunks = [c.strip() for c in content.split('\n\n') if c.strip()]
                
                for i, chunk in enumerate(chunks):
                    ids.append(f"{filename}_{i}")
                    documents.append(chunk)
                    metadatas.append({"source": filename})
                    count += 1
        
        if documents:
            # Upsert (atualiza se existir, insere se novo)
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"Indexados {count} fragmentos de texto.")
        else:
            print("Nenhum documento encontrado ou documentos vazios.")

    def search(self, query, n_results=3):
        """Busca os trechos mais relevantes para a pergunta"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0] # Retorna lista de textos encontrados
