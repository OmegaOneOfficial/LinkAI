import streamlit as st
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Gemini Chatbot", page_icon="♊")

st.title("♊ Mi IA Gemini")
st.write(
    "Este es un chatbot que utiliza el modelo **Gemini 1.5 Flash** de Google. "
    "He configurado tu API Key directamente en el código."
)

# Configuración de la API Key que proporcionaste
# Nota: Recuerda borrar el mensaje anterior donde pusiste la clave por seguridad.
GEMINI_API_KEY = "AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug"
genai.configure(api_key=GEMINI_API_KEY)

# Inicializar el modelo
model = genai.GenerativeModel('gemini-1.5-flash')

# El historial de Gemini usa "model" en vez de "assistant"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada de chat
if prompt := st.chat_input("¿En qué puedo ayudarte?"):

    # Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        # Preparamos el historial para Gemini (cambiando assistant por model)
        history_for_gemini = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
            for m in st.session_state.messages[:-1]
        ]
        
        chat = model.start_chat(history=history_for_gemini)
        
        # Usamos stream para que la respuesta aparezca poco a poco
        response = chat.send_message(prompt, stream=True)
        
        # Función para iterar sobre el stream y mostrarlo en Streamlit
        def stream_generator():
            for chunk in response:
                yield chunk.text

        full_response = st.write_stream(stream_generator())
    
    # Guardar la respuesta completa en el historial
    st.session_state.messages.append({"role": "assistant", "content": full_response})
