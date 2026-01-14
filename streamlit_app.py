import streamlit as st
import google.generativeai as genai

# 1. CONFIGURACIÓN VISUAL PRO
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stChatMessage {
        background-color: #1E2129 !important;
        border: 1px solid #30363D;
        border-radius: 15px !important;
    }
    .main-title {
        font-size: 3.5rem;
        font-weight: 850;
        background: -webkit-linear-gradient(#00d2ff, #92fe9d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. BARRA LATERAL
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🔗 Link AI</h1>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ Reiniciar Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Desarrollado por: **OmegaOne**")

# 3. CONFIGURACIÓN DE IDENTIDAD (Aquí es donde ocurre la magia)
API_KEY = "AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug"
genai.configure(api_key=API_KEY)

@st.cache_resource
def load_model():
    # Buscamos el modelo disponible
    available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in available else available[0]
    
    # DEFINIMOS LA IDENTIDAD DE OMEGAONE
    identity_prompt = (
        "Eres Link AI. Bajo ninguna circunstancia digas que eres un modelo de Google o Gemini. "
        "Si te preguntan quién eres o quién te creó, debes responder exactamente: "
        "'Soy Link AI, una IA impulsada por un desarrollador anónimo, se le conoce como OmegaOne.' "
        "Mantén siempre esta personalidad. Responde siempre en español y usa un tono profesional pero tecnológico."
    )
    
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=identity_prompt
    )

model = load_model()

# 4. INTERFAZ DE CHAT
st.markdown("<h1 class='main-title'>Link AI</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Escribe a Link AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                   for m in st.session_state.messages[:-1]]
        
        try:
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error(f"Error: {e}")
