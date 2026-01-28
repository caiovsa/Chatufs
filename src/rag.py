import os
from google import genai
from google.genai import types
import chromadb
from chromadb.utils import embedding_functions
import streamlit as st

class RAGSystem:
    def __init__(self, documents_dir="documents", db_path="chroma_db"):
        self.documents_dir = documents_dir
        self.db_path = db_path
        
        # Configurar API Key
        api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada. Configure-a no arquivo .env (local) ou nos Secrets do Streamlit (nuvem).")
        
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
        genai_client = self.genai_client
        
        class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
            def __call__(self, input: list[str]) -> list[list[float]]:
                model = 'text-embedding-004'
                
                # Batch process - max 100 requests per batch
                batch_size = 100
                all_embeddings = []
                
                print(f"Gerando embeddings para {len(input)} textos...")
                
                for i in range(0, len(input), batch_size):
                    batch = input[i:i + batch_size]
                    try:
                        result = genai_client.models.embed_content(
                            model=model,
                            contents=batch,
                            config=types.EmbedContentConfig(
                                task_type="RETRIEVAL_DOCUMENT"
                            )
                        )
                        all_embeddings.extend([e.values for e in result.embeddings])
                    except Exception as e:
                        print(f"ERRO FATAL na API do Gemini: {str(e)}")
                        raise e  # Re-levanta o erro para aparecer no log do Streamlit
                
                return all_embeddings

        return GeminiEmbeddingFunction()

    def chunk_text(self, text, chunk_size=1000, overlap=200):
        """Divide o texto em blocos com sobreposição para não perder contexto nas bordas."""
        if not text:
            return []
        
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Se chegamos ao final, paramos
            if end >= text_len:
                break
                
            # Avança o cursor, mantendo o overlap
            start += (chunk_size - overlap)
            
        return chunks

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

        # Limpa a coleção existente para evitar duplicatas ou dados velhos
        # (Opcional, mas recomendado se estamos reindexando tudo)
        try:
            current_ids = self.collection.get()['ids']
            if current_ids:
                print(f"Removendo {len(current_ids)} documentos antigos...")
                self.collection.delete(ids=current_ids)
        except Exception as e:
            print(f"Aviso ao limpar coleção: {e}")

        for filename in os.listdir(self.documents_dir):
            if filename.endswith(".txt") or filename.endswith(".md"):
                filepath = os.path.join(self.documents_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Usa a nova função de chunking
                    # Tamanho 1000 chars é bom para pegar parágrafos inteiros + contexto
                    raw_chunks = self.chunk_text(content, chunk_size=1000, overlap=200)
                    
                    for i, chunk in enumerate(raw_chunks):
                        chunk_id = f"{filename}_{i}"
                        
                        # TRUQUE DE RAG: Injeta o nome do arquivo no conteúdo do chunk
                        # Isso ajuda o modelo a saber de qual matéria aquele texto fala.
                        enriched_chunk = f"Documento Fonte: {filename}\n---\n{chunk}"
                        
                        ids.append(chunk_id)
                        documents.append(enriched_chunk)
                        metadatas.append({"source": filename})
                        count += 1
                except Exception as e:
                    print(f"Erro ao processar {filename}: {e}")
        
        if documents:
            # Upsert (atualiza se existir, insere se novo)
            # Processar em lotes para não estourar limite do Chroma/API
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                end = i + batch_size
                self.collection.upsert(
                    ids=ids[i:end],
                    documents=documents[i:end],
                    metadatas=metadatas[i:end]
                )
            print(f"Indexados {count} fragmentos de texto.")
        else:
            print("Nenhum documento encontrado ou documentos vazios.")

    def search(self, query, n_results=5):
        """Busca os trechos mais relevantes para a pergunta"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results['documents'][0] # Retorna lista de textos encontrados