import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

# --- 2. UI MINIMALISTA REFINADA ---
st.markdown("""
    <style>
    /* Fondo Gris Carbón */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    
    /* Brand Link AI arriba a la derecha */
    .brand-top-right {
        position: fixed;
        top: 20px;
        right: 160px; /* Ajustado para que no choque */
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        color: #FFFFFF;
        z-index: 1001;
        opacity: 0.8;
    }

    /* Botón Cerrar Sesión (Arriba a la Derecha) */
    .logout-container {
        position: fixed;
        top: 15px;
        right: 20px;
        z-index: 1000;
    }
    
    /* Botones Sidebar */
    .stButton>button {
        border-radius: 10px !important;
        background-color: transparent !important;
        border: 1px solid #444 !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
    }
    
    /* Icono de Enviar Blanco en el Chat Input */
    .stChatInput button svg {
        fill: white !important;
        color: white !important;
    }
    
    /* Burbujas de chat */
    div.stChatMessage {
        border-radius: 20px !important;
        background-color: #1E1E1E !important;
        border: 1px solid #2A2A2A !important;
        margin-bottom: 15px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F0F0F !important;
        border-right: 1px solid #252525 !important;
    }

    /* Ocultar elementos de Streamlit */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('linkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT, created_at DATETIME)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (session_id INTEGER, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    conn.close()

init_db()

# --- 4. ACCESO ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center; color:white; margin-top:10vh;'>LINK AI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab_log, tab_reg = st.tabs(["Acceder", "Registrar"])
        with tab_log:
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.button("LOG IN", use_container_width=True):
                conn = sqlite3.connect('linkai_pro.db')
                res = conn.execute("SELECT password FROM users WHERE username=?", (u,)).fetchone()
                if res and hashlib.sha256(p.encode()).hexdigest() == res[0]:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else: st.error("Error.")
        with tab_reg:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Clave", type="password")
            if st.button("REGISTRAR", use_container_width=True):
                conn = sqlite3.connect('linkai_pro.db')
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?)", (nu, hashlib.sha256(np.encode()).hexdigest(), "user"))
                    conn.commit()
                    st.success("Listo.")
                except: st.error("Existe.")
    st.stop()

# --- HEADER FIJO ---
st.markdown('<div class="brand-top-right">Link AI</div>', unsafe_allow_html=True)
st.markdown('<div class="logout-container">', unsafe_allow_html=True)
if st.button("Cerrar Sesión", key="logout_btn"):
    st.session_state.logged_in = False
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. CONFIGURACIÓN IA (CORREGIDO A models/...) ---
genai.configure(api_key="AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug")

# Aquí usamos el prefijo exacto para evitar errores de conexión
MODEL_NAME = 'models/gemini-1.5-flash'

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=f"Soy Link AI una IA impulsada por un desarrollador anonimo, se le conoce como OmegaOne. Hablo con {st.session_state.username}.",
    safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
)

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🔗 Link AI")
    # Botón Nuevo Chat con icono grande
    if st.button("＋", use_container_width=True, help="Nuevo Chat"):
        st.session_state.current_session_id = None
        st.rerun()
    
    st.markdown("---")
    conn = sqlite3.connect('linkai_pro.db')
    chats = conn.execute("SELECT id, title FROM chat_sessions WHERE username=? ORDER BY created_at DESC LIMIT 12", (st.session_state.username,)).fetchall()
    for cid, title in chats:
        # Icono de mensaje minimalista antes del texto
        if st.button(f"󰭹 {title[:15]}...", key=f"c_{cid}", use_container_width=True):
            st.session_state.current_session_id = cid
            st.rerun()

# --- 7. CHAT ---
if st.session_state.get("current_session_id"):
    conn = sqlite3.connect('linkai_pro.db')
    msgs = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC", (st.session_state.current_session_id,)).fetchall()
    for r, c in msgs:
        with st.chat_message(r): st.markdown(c)
else:
    # Pantalla de bienvenida minimalista
    st.markdown(f"<div style='text-align:center; margin-top:25vh; color:#666;'><h2>Hola, {st.session_state.username}</h2><p>Inicia una conversación con Link AI</p></div>", unsafe_allow_html=True)

# Entrada de chat con botón de enviar icono blanco
if prompt := st.chat_input("Escribe a Link AI..."):
    conn = sqlite3.connect('linkai_pro.db')
    if not st.session_state.get("current_session_id"):
        cursor = conn.execute("INSERT INTO chat_sessions (username, title, created_at) VALUES (?,?,?)", (st.session_state.username, prompt[:20], datetime.now()))
        st.session_state.current_session_id = cursor.lastrowid
        conn.commit()

    with st.chat_message("user"): st.markdown(prompt)
    conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "user", prompt, datetime.now()))
    conn.commit()

    with st.chat_message("assistant"):
        ph = st.empty()
        full_res = ""
        try:
            # Reconstruir historial (ventana de 8 mensajes)
            hist_db = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC LIMIT 8", (st.session_state.current_session_id,)).fetchall()
            history = [{"role": "user" if r == "user" else "model", "parts": [c]} for r, c in hist_db[:-1]]
            
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    ph.markdown(full_res + "▌")
            ph.markdown(full_res)
            conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "assistant", full_res, datetime.now()))
            conn.commit()
        except Exception as e:
            if "429" in str(e):
                st.error("🚀 Límite alcanzado. Espera 60s.")
            else:
                st.error(f"Error: {e}")
