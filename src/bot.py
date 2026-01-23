import os
import google.generativeai as genai

class GeminiBot:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada no .env")
        
        genai.configure(api_key=api_key)
        
        # Configuração do modelo
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
        )
        self.chat = self.model.start_chat(history=[])

    def generate_response(self, query, context_chunks):
        """Gera resposta baseada na pergunta e no contexto recuperado"""
        
        context_text = "\n\n".join(context_chunks)
        
        prompt = f"""
Você é um assistente útil e preciso. Use APENAS as informações fornecidas no contexto abaixo para responder à pergunta do usuário.
Se a informação não estiver no contexto, diga que não sabe com base nos documentos fornecidos.

CONTEXTO:
{context_text}

PERGUNTA:
{query}
"""
        response = self.chat.send_message(prompt)
        return response.text
