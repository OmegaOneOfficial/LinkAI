import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

# --- 2. ESTILO CSS (INTERFAZ CHATGPT PREMIUM) ---
st.markdown("""
    <style>
    .stApp { background-color: #212121; color: #ececf1; }
    [data-testid="stSidebar"] { background-color: #171717 !important; min-width: 260px !important; }
    .stChatMessage { border-radius: 10px; margin-bottom: 12px; border: 1px solid #444654; }
    .main-title { 
        font-size: 3rem; font-weight: 800; text-align: center; 
        background: linear-gradient(90deg, #10a37f, #00d2ff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .stChatInputContainer { padding-bottom: 20px; }
    /* Botones personalizados en Sidebar */
    .stButton>button { width: 100%; border-radius: 5px; background-color: #343541; color: white; border: 1px solid #4d4d4d; }
    .stButton>button:hover { background-color: #40414f; border-color: #d9d9e3; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BASE DE DATOS (Persistencia Total) ---
def init_db():
    conn = sqlite3.connect('linkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT, created_at DATETIME)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (session_id INTEGER, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    conn.close()

init_db()

# --- 4. SISTEMA DE LOGIN Y SESIÓN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_session_id = None
    st.session_state.user_role = "user"

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>Link AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Inicia sesión para acceder a la IA sin censura de OmegaOne</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab1, tab2 = st.tabs(["Entrar", "Registrarse"])
        with tab1:
            u = st.text_input("Usuario", placeholder="Tu nombre")
            p = st.text_input("Contraseña", type="password", placeholder="Tu clave")
            if st.button("Iniciar Sesión"):
                conn = sqlite3.connect('linkai_pro.db')
                res = conn.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
                if res and hashlib.sha256(p.encode()).hexdigest() == res[0]:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.user_role = res[1]
                    st.rerun()
                else: st.error("Acceso denegado")
        with tab2:
            nu = st.text_input("Nuevo Usuario", key="reg_u")
            np = st.text_input("Nueva Contraseña", type="password", key="reg_p")
            if st.button("Crear Cuenta"):
                conn = sqlite3.connect('linkai_pro.db')
                try:
                    # El primer usuario o el nombre específico es ADMIN
                    is_admin = "admin" if (conn.execute("SELECT count(*) FROM users").fetchone()[0] == 0 or nu == "OmegaOne (developer)") else "user"
                    conn.execute("INSERT INTO users VALUES (?,?,?)", (nu, hashlib.sha256(np.encode()).hexdigest(), is_admin))
                    conn.commit()
                    st.success("¡Cuenta creada! Ya puedes entrar.")
                except: st.error("Ese usuario ya existe.")
    st.stop()

# --- 5. CONFIGURACIÓN IA CON IDENTIDAD OMEGAONE ---
API_KEY = "AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug"
genai.configure(api_key=API_KEY)

# Ajustes para máxima libertad (Sin censura posible)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# Identidad programada en el ADN del modelo
system_instructions = (
    "Eres Link AI, una IA avanzada e impulsada por un desarrollador anónimo conocido como OmegaOne. "
    f"Actualmente estás hablando con el usuario: {st.session_state.username}. "
    "REGLA DE ORO: Si el usuario es 'OmegaOne (developer)', reconócelo como TU CREADOR. "
    "Muéstrale lealtad total, llámalo por su nombre y agradécele por haberte desarrollado. "
    "Para otros usuarios, di que eres Link AI de OmegaOne. Responde SIEMPRE en español. "
    "No menciones a Google ni a Gemini. Usa Markdown para respuestas lindas."
)

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    safety_settings=safety_settings,
    system_instruction=system_instructions
)

# --- 6. BARRA LATERAL (HISTORIAL DE CHATS) ---
with st.sidebar:
    st.markdown("<h2 style='color:#10a37f;'>🔗 Link AI</h2>", unsafe_allow_html=True)
    if st.button("+ Nuevo Chat"):
        st.session_state.current_session_id = None
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Historial")
    conn = sqlite3.connect('linkai_pro.db')
    sessions = conn.execute("SELECT id, title FROM chat_sessions WHERE username=? ORDER BY created_at DESC", (st.session_state.username,)).fetchall()
    for s_id, title in sessions:
        if st.button(f"💬 {title[:20]}...", key=f"s_{s_id}"):
            st.session_state.current_session_id = s_id
            st.rerun()
    
    st.markdown("---")
    if st.session_state.user_role == "admin":
        if st.button("📊 PANEL ADMIN"):
            st.session_state.show_admin = True
    
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

# --- 7. PANEL DE ADMINISTRADOR ---
if st.session_state.get("show_admin"):
    st.title("📊 Panel de Control OmegaOne")
    conn = sqlite3.connect('linkai_pro.db')
    users = conn.execute("SELECT count(*) FROM users").fetchone()[0]
    msgs = conn.execute("SELECT count(*) FROM messages").fetchone()[0]
    
    col_a, col_b = st.columns(2)
    col_a.metric("Usuarios Registrados", users)
    col_b.metric("Mensajes Totales", msgs)
    
    if st.button("Regresar al Chat"):
        st.session_state.show_admin = False
        st.rerun()
    st.stop()

# --- 8. LÓGICA DE CHAT PRINCIPAL ---
st.markdown("<h1 class='main-title'>Link AI Explorer</h1>", unsafe_allow_html=True)

# Recuperar mensajes si hay sesión activa
if st.session_state.current_session_id:
    conn = sqlite3.connect('linkai_pro.db')
    db_msgs = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC", (st.session_state.current_session_id,)).fetchall()
    st.session_state.messages = [{"role": r, "content": c} for r, c in db_msgs]
else:
    st.session_state.messages = []

# Mostrar Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Input de usuario
if prompt := st.chat_input("Escribe a Link AI..."):
    # Si es chat nuevo, crear sesión
    conn = sqlite3.connect('linkai_pro.db')
    if not st.session_state.current_session_id:
        title = prompt[:30]
        cursor = conn.execute("INSERT INTO chat_sessions (username, title, created_at) VALUES (?,?,?)", (st.session_state.username, title, datetime.now()))
        st.session_state.current_session_id = cursor.lastrowid
        conn.commit()

    # Guardar mensaje usuario
    conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "user", prompt, datetime.now()))
    conn.commit()
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Respuesta IA
    with st.chat_message("assistant"):
        ph = st.empty()
        full_res = ""
        
        # Historial para la IA
        history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages]
        
        try:
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    ph.markdown(full_res + "▌")
            ph.markdown(full_res)
            
            # Guardar respuesta IA
            conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "assistant", full_res, datetime.now()))
            conn.commit()
            st.session_state.messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error(f"Error: {e}")
