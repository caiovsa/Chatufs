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
    page_icon="images/image.png",
    layout="wide"
)

# --- Estilo para o Chat Bubble Flutuante ---
st.markdown("""
    <style>
    /* Estiliza o container do popover para ficar fixo no canto */
    div[data-testid="stPopover"] {
        position: fixed !important;
        bottom: 120px !important;
        right: 30px !important;
        width: auto !important;
        z-index: 9999 !important;
    }
    /* Estiliza o botão do popover */
    div[data-testid="stPopover"] > button {
        border-radius: 50%;
        width: 60px;
        height: 60px;
        background-color: #007bff;
        color: white;
        border: none;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stPopover"] > button:hover {
        background-color: #0056b3;
    }
    </style>
""", unsafe_allow_html=True)

# Título e Subtítulo
col1, col2, _ = st.columns([1, 2, 10])
with col1:
    st.image("images/image.png", width=100)
with col2:
    st.image("images/image2.png", width=200)

st.title("Chat Virtual UFS")
st.markdown("Assistente virtual para tirar dúvidas sobre grades curriculares e normas da UFS.")

# --- Inicialização do Sistema ---
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

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Configurações")
    if st.button("🔄 Atualizar Base de Conhecimento"):
        if rag:
            with st.status("Processando documentos...", expanded=True) as status:
                st.write("Lendo arquivos da pasta /documents...")
                rag.load_documents()
                status.update(label="Base atualizada com sucesso!", state="complete", expanded=False)
                st.success("Tudo pronto!")
        else:
            st.error("Sistema RAG não foi inicializado.")

# --- Lógica de Chat Unificada ---
def process_input(prompt_text, container=st):
    # 1. Mostra a pergunta
    with container.chat_message("user"):
        st.markdown(prompt_text)
    st.session_state.messages.append({"role": "user", "content": prompt_text})

    # 2. Processa a resposta
    with container.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            with st.spinner("Buscando..."):
                context_chunks = rag.search(prompt_text, n_results=5)
            
            full_response = bot.generate_response(prompt_text, context_chunks)
            message_placeholder.markdown(full_response)
            
            with st.expander("📚 Fontes"):
                for i, chunk in enumerate(context_chunks):
                    st.markdown(f"**Fonte {i+1}:**\n{chunk}")
        except Exception as e:
            full_response = f"❌ Erro: {str(e)}"
            message_placeholder.markdown(full_response)

    # 3. Salva no histórico
    st.session_state.messages.append({"role": "assistant", "content": full_response})


# --- Gerenciamento do Estado ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Exibição na Página Principal ---
# Mostra histórico na página principal
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input da Página Principal
if prompt_main := st.chat_input("Digite sua dúvida (Chat Principal)..."):
    process_input(prompt_main, container=st)


# --- Chat Bubble (Popover) ---
# O Popover flutuante
with st.popover("💬"):
    st.subheader("Atendimento UFS")
    
    # Container para mensagens dentro do popover
    popover_container = st.container(height=400)
    
    # Renderiza o histórico dentro do popover também (opcional, mas bom para contexto)
    with popover_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input do Popover
    if prompt_popover := st.chat_input("Como posso ajudar? (Chat Flutuante)"):
        # Processa usando o container do popover para renderizar a resposta LÁ dentro
        # Nota: Ao atualizar o session_state, a página recarrega e atualiza o principal também.
        
        # Hack: Precisamos processar e exibir dentro do container do popover agora
        # Mas como o st.chat_input causa rerun, a lógica acima processaria?
        # Vamos reusar a função, mas passando o container certo.
        
        # Adiciona mensagem do usuário ao histórico e visual
        with popover_container.chat_message("user"):
            st.markdown(prompt_popover)
        st.session_state.messages.append({"role": "user", "content": prompt_popover})

        # Resposta do assistente
        with popover_container.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                with st.spinner("Buscando..."):
                    context_chunks = rag.search(prompt_popover, n_results=5)
                
                full_response = bot.generate_response(prompt_popover, context_chunks)
                message_placeholder.markdown(full_response)
                
            except Exception as e:
                full_response = f"❌ Erro: {str(e)}"
                message_placeholder.markdown(full_response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.rerun()
