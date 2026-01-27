import streamlit as st
import os
import time
from src.rag import RAGSystem
from src.bot import GeminiBot
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

# Configuração da Página
st.set_page_config(
    page_title="Chatbot UFS - STI",
    page_icon="🎓",
    layout="wide"
)

# Título e Subtítulo
st.title("🎓 Chatbot UFS")
st.markdown("Assistente virtual para tirar dúvidas sobre grades curriculares e normas da UFS.")

# --- Inicialização do Sistema (Cacheado para não recarregar a cada interação) ---
@st.cache_resource
def load_system():
    try:
        rag = RAGSystem()
        bot = GeminiBot()
        return rag, bot
    except Exception as e:
        st.error(f"Erro ao inicializar o sistema: {e}")
        return None, None

rag, bot = load_system()

# --- Sidebar (Barra Lateral) ---
with st.sidebar:
    st.header("⚙️ Configurações")
    
    # Botão para recarregar documentos
    if st.button("🔄 Atualizar Base de Conhecimento"):
        if rag:
            with st.status("Processando documentos...", expanded=True) as status:
                st.write("Lendo arquivos da pasta /documents...")
                rag.load_documents()
                status.update(label="Base atualizada com sucesso!", state="complete", expanded=False)
                st.success("Tudo pronto! A IA agora tem acesso aos novos arquivos.")
        else:
            st.error("Sistema RAG não foi inicializado corretamente.")

    st.divider()
    st.info("""
    **Como funciona:**
    1. O robô lê os arquivos na pasta `documents/`.
    2. Divide em pedaços pequenos.
    3. Quando você pergunta, ele busca os pedaços mais parecidos.
    4. O Gemini gera a resposta baseada neles.
    """)

# --- Gerenciamento do Chat ---

# Inicializa histórico se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("Digite sua dúvida sobre as disciplinas..."):
    # 1. Mostra a pergunta do usuário
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Processa a resposta
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # Passo 1: Busca no RAG
            with st.spinner("Pesquisando nos documentos..."):
                context_chunks = rag.search(prompt, n_results=5)
            
            # Passo 2: Gera resposta com o Gemini
            # Simula stream (opcional, mas fica bonito)
            full_response = bot.generate_response(prompt, context_chunks)
            
            message_placeholder.markdown(full_response)
            
            # Adiciona um "Expander" para ver o contexto usado (Transparência)
            with st.expander("📚 Ver fontes consultadas"):
                for i, chunk in enumerate(context_chunks):
                    st.markdown(f"**Trecho {i+1}:**\n\n{chunk}")
                    st.divider()

        except Exception as e:
            full_response = f"❌ Desculpe, ocorreu um erro: {str(e)}"
            message_placeholder.markdown(full_response)

    # 3. Salva no histórico
    st.session_state.messages.append({"role": "assistant", "content": full_response})
