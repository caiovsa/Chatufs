import os
from dotenv import load_dotenv
from src.rag import RAGSystem

def test_rag_offline():
    load_dotenv()
    print("Testando inicialização do RAG e leitura de arquivos...")
    
    try:
        # Mocking API Key para teste de estrutura (não vai funcionar o embedding real)
        os.environ["GEMINI_API_KEY"] = "dummy_key"
        
        rag = RAGSystem()
        rag.load_documents()
        
        print("\n✅ Estrutura de pastas e ChromaDB: OK")
        print(f"✅ Arquivos encontrados: {os.listdir('documents')}")
        
    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")

if __name__ == "__main__":
    test_rag_offline()

