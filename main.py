import os
from dotenv import load_dotenv
from src.rag import RAGSystem
from src.bot import GeminiBot

def main():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Verificar API Key
    if os.getenv("GEMINI_API_KEY") == "sua_chave_aqui":
        print("ERRO: Configure sua GEMINI_API_KEY no arquivo .env antes de rodar!")
        return

    print("Inicializando sistema...")
    
    try:
        # Inicializar RAG
        rag = RAGSystem()
        # Carregar documentos (pode comentar essa linha se quiser carregar apenas uma vez)
        rag.load_documents()
        
        # Inicializar Bot
        bot = GeminiBot()
        
        print("\n=== Chatbot UFS (RAG + Gemini) ===")
        print("Digite 'sair' para encerrar.\n")
        
        while True:
            user_input = input("Você: ")
            if user_input.lower() in ['sair', 'exit', 'quit']:
                break
                
            # 1. Buscar contexto relevante
            print("🔍 Buscando informações...")
            relevant_chunks = rag.search(user_input)
            
            # 2. Gerar resposta
            print("🤖 Gerando resposta...")
            response = bot.generate_response(user_input, relevant_chunks)
            
            print(f"\nGemini: {response}\n")
            print("-" * 50)
            
    except Exception as e:
        print(f"\nUm erro ocorreu: {e}")

if __name__ == "__main__":
    main()
