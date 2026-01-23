import os
from google import genai
from google.genai import types

class GeminiBot:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no .env")
        
        self.client = genai.Client(api_key=api_key)
        
        # Configuração do modelo via dicionário ou objeto de configuração
        # Ajustado para usar os tipos da nova SDK se necessário, mas dicionários simples costumam funcionar
        # ou passando parâmetros diretos no create.
        
        self.chat = self.client.chats.create(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
        )

    def generate_response(self, query, context_chunks=None):
        """Gera resposta baseada na pergunta e no contexto recuperado (opcional)"""
        
        if context_chunks:
            context_text = "\n\n".join(context_chunks)
            prompt = f"""
Você é um assistente útil e preciso. Use APENAS as informações fornecidas no contexto abaixo para responder à pergunta do usuário.
Se a informação não estiver no contexto, diga que não sabe com base nos documentos fornecidos.

CONTEXTO:
{context_text}

PERGUNTA:
{query}
"""
        else:
            # Modo padrão sem RAG
            prompt = query

        response = self.chat.send_message(prompt)
        return response.text