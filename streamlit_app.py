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
    # Tabla de usuarios (UNIQUE para que no se repitan nombres)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Tabla de chats
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
        return False # El nombre ya existe
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

# --- PANTALLA DE ACCESO (Solo se muestra si no está logueado) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #00d2ff;'>🔗 Bienvenido a Link AI</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
        
        with tab1:
            with st.form("login"):
                u = st.text_input("Nombre de usuario")
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
                new_u = st.text_input("Elige un nombre de usuario")
                new_p = st.text_input("Crea una contraseña", type="password")
                if st.form_submit_button("Registrarse"):
                    if save_user(new_u, new_p):
                        st.success("¡Cuenta creada! Ya puedes iniciar sesión.")
                    else:
                        st.error("Ese nombre ya está ocupado. Elige otro.")
    st.stop() # Detiene el script aquí hasta que se loguee

# --- SI LLEGAMOS AQUÍ, EL USUARIO YA ESTÁ DENTRO ---
# Configuración de la IA
API_KEY = "AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction="Soy Link AI una IA impulsada por un desarrollador anonimo, se le conoce como OmegaOne. Responde siempre en español."
)

# Barra lateral
with st.sidebar:
    st.markdown(f"### Hola, **{st.session_state.username}**")
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()
    st.markdown("---")
    st.caption("Link AI v1.5 por OmegaOne")

# Chat
st.markdown(f"<h2 style='text-align: center;'>Panel de Link AI</h2>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history(st.session_state.username)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("¿Qué tienes en mente?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_chat(st.session_state.username, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} 
                   for m in st.session_state.messages[:-1]]
        
        chat = model.start_chat(history=history)
        response = chat.send_message(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                full_res += chunk.text
                placeholder.markdown(full_res + "▌")
        placeholder.markdown(full_res)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
        save_chat(st.session_state.username, "assistant", full_res)
