import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

# --- BASE DE DATOS (SQLite) ---
def init_db():
    conn = sqlite3.connect('linkai_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats 
                 (username TEXT, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_user(username, password):
    conn = sqlite3.connect('linkai_data.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(str.encode(password)).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('linkai_data.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(str.encode(password)).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    data = c.fetchone()
    conn.close()
    return data

def save_chat(username, role, content):
    conn = sqlite3.connect('linkai_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO chats (username, role, content) VALUES (?, ?, ?)", (username, role, content))
    conn.commit()
    conn.close()

def load_chat_history(username):
    conn = sqlite3.connect('linkai_data.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM chats WHERE username = ? ORDER BY timestamp ASC", (username,))
    data = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in data]

init_db()

# --- CONTROL DE SESIÓN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- PANTALLA DE ACCESO ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #00d2ff;'>🔗 Bienvenido a Link AI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
        with tab1:
            with st.form("login"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Entrar"):
                    if login_user(u, p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
        with tab2:
            with st.form("signup"):
                new_u = st.text_input("Nombre de usuario")
                new_p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Registrarse"):
                    if save_user(new_u, new_p):
                        st.success("¡Cuenta creada!")
                    else:
                        st.error("El nombre ya existe")
    st.stop()

# --- CONFIGURACIÓN DE IA (CON DETECCIÓN DE MODELO PARA EVITAR 404) ---
API_KEY = "AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug"
genai.configure(api_key=API_KEY)

@st.cache_resource
def get_safe_model():
    """Busca el modelo correcto para evitar el error NotFound"""
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Prioridad de modelos
        for target in ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']:
            if target in available:
                return genai.GenerativeModel(
                    model_name=target,
                    system_instruction="Soy Link AI una IA impulsada por un desarrollador anonimo, se le conoce como OmegaOne. Responde siempre en español."
                )
        return genai.GenerativeModel(available[0])
    except:
        return genai.GenerativeModel('gemini-pro')

model = get_safe_model()

# --- INTERFAZ PRINCIPAL ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.username}")
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown("---")
    st.caption("Link AI v2.0 - OmegaOne")

st.markdown("<h1 style='text-align: center;'>Link AI Explorer</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history(st.session_state.username)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("¿En qué puedo ayudarte?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_chat(st.session_state.username, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        # Filtramos historial para Gemini
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
            save_chat(st.session_state.username, "assistant", full_res)
        except Exception as e:
            st.error(f"Error de conexión: {e}")
