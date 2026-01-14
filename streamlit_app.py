import streamlit as st
import google.generativeai as genai

# 1. Configuración visual y de página
st.set_page_config(
    page_title="Link AI", 
    page_icon="🔗", 
    layout="centered"
)

# Estilo personalizado para mejorar la interfaz
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Barra lateral (Sidebar)
with st.sidebar:
    st.title("🔗 Link AI")
    st.info("Tu Asistente Inteligente impulsado por Google Gemini.")
    
    # Botón para limpiar el chat
    if st.button("Limpiar Historial"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.write("### Sobre Link AI")
    st.caption("Versión 1.0.0")
    st.caption("Hecho con ❤️ y Streamlit")

# 3. Configuración de la IA
API_KEY = "AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug"
genai.configure(api_key=API_KEY)

# Función para encontrar el modelo que NO de error 404
@st.cache_resource
def load_model():
    try:
        # Intentamos listar y buscar el mejor disponible
        available_models = [m.name for m in genai.list_models() 
                            if 'generateContent' in m.supported_generation_methods]
        
        # Prioridad: 1.5 Flash -> 1.5 Pro -> Pro (antiguo)
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if target in available_models:
                return genai.GenerativeModel(target)
        
        # Si no encuentra los anteriores, usa el primero que responda
        return genai.GenerativeModel(available_models[0])
    except:
        # Último recurso si falla el listado
        return genai.GenerativeModel('gemini-pro')

model = load_model()

# 4. Historial de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Interacción Principal
if prompt := st.chat_input("Escribe un mensaje en Link AI..."):
    
    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta de la IA
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # Traducir historial para Gemini
            history = [
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in st.session_state.messages[:-1]
            ]
            
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Link AI tuvo un problema: {str(e)}")
