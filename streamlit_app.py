import streamlit as st
import google.generativeai as genai

# 1. Configuración de la página
st.set_page_config(page_title="Nexos AI", page_icon="♊")

# Título de la aplicación
st.title("🤖 Nexos AI")
st.markdown("---")

# 2. Configuración de la API Key
# He puesto la clave que compartiste, pero si falla, recuerda crear una nueva en Google AI Studio
API_KEY = "AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug"
genai.configure(api_key=API_KEY)

# 3. Inicializar el modelo con manejo de errores
try:
    # Usamos la ruta completa del modelo para evitar el error 'NotFound'
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"Error al cargar el modelo: {e}")

# 4. Inicializar el historial del chat (Streamlit usa roles 'user' y 'assistant')
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Lógica del Chat
if prompt := st.chat_input("¿En qué puedo ayudarte?"):
    
    # Mostrar y guardar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta de la IA
    with st.chat_message("assistant"):
        message_placeholder = st.empty() # Espacio para el efecto de escritura
        full_response = ""
        
        try:
            # PREPARACIÓN DEL HISTORIAL (Crucial para Gemini)
            # Convertimos 'assistant' de Streamlit a 'model' de Google
            history_gemini = []
            for m in st.session_state.messages[:-1]:
                role = "user" if m["role"] == "user" else "model"
                history_gemini.append({"role": role, "parts": [m["content"]]})

            # Iniciar chat con memoria
            chat = model.start_chat(history=history_gemini)
            
            # Enviar mensaje con streaming
            response = chat.send_message(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # Guardar respuesta en el historial
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Error en la API: {e}")
            if "NotFound" in str(e):
                st.info("💡 Tip: Revisa si tu API Key está activa o prueba cambiando el nombre del modelo a 'gemini-1.5-pro'.")
