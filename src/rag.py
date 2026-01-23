import os
from google import genai
from google.genai import types
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
        
        # Inicializar Cliente do Google Gen AI (Novo SDK)
        self.genai_client = genai.Client(api_key=api_key)
        
        # Inicializar ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Usar função de embedding customizada do Google
        self.embedding_fn = self._create_embedding_fn()
        
        # Criar ou obter coleção
        self.collection = self.client.get_or_create_collection(
            name="documents_collection",
            embedding_function=self.embedding_fn
        )

    def _create_embedding_fn(self):
        # Wrapper simples para compatibilidade com ChromaDB
        # Captura o client do escopo externo (self.genai_client)
        genai_client = self.genai_client
        
        class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
            def __call__(self, input: list[str]) -> list[list[float]]:
                # Modelo de embedding do Google
                model = 'text-embedding-004'
                
                # A nova SDK suporta lista de conteudos diretamente, mas para garantir
                # o formato exato que o Chroma espera (lista de lista de floats),
                # vamos processar. O SDK retorna um objeto com .embeddings
                
                try:
                    result = genai_client.models.embed_content(
                        model=model,
                        contents=input,
                        config=types.EmbedContentConfig(
                            task_type="RETRIEVAL_DOCUMENT"
                        )
                    )
                    # Extrair os valores dos embeddings
                    return [e.values for e in result.embeddings]
                except Exception as e:
                    print(f"Erro ao gerar embeddings: {e}")
                    return []

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
                
                # Chunking simplificado
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