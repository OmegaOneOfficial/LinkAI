import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

# --- 2. CSS AGRESIVO (CLONACIÓN TOTAL) ---
st.markdown("""
    <style>
    /* Reset total y fondo */
    .stApp { background-color: #131314; color: #e3e3e3; }
    header, footer, [data-testid="stHeader"] {display: none !important;}
    
    /* SIDEBAR ULTRA ESTRECHO */
    [data-testid="stSidebar"] {
        width: 68px !important;
        background-color: #1e1f20 !important;
        border: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { padding: 10px 5px; }

    /* BOTONES SIDEBAR CUADRADOS TRANSPARENTES */
    .stButton>button {
        background-color: transparent !important;
        border: none !important;
        color: #e3e3e3 !important;
        font-size: 1.5rem !important;
        width: 100% !important;
        aspect-ratio: 1/1;
        display: flex; justify-content: center; align-items: center;
        margin-bottom: 10px;
        transition: background 0.2s;
    }
    .stButton>button:hover { background-color: #333537 !important; border-radius: 12px !important; }

    /* BARRA SUPERIOR */
    .top-nav {
        position: fixed; top: 0; left: 0; right: 0; height: 64px;
        background-color: #131314; display: flex; align-items: center;
        padding: 0 20px; z-index: 1000;
    }
    .brand { font-size: 1.3rem; font-weight: 500; display: flex; align-items: center; gap: 8px; }
    .chat-title { position: absolute; left: 50%; transform: translateX(-50%); color: #c4c7c5; font-size: 0.9rem; }
    
    /* ELIMINAR BURBUJAS DE MENSAJES */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 1rem 15% !important; /* Margen lateral como la imagen */
    }
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* ESTILO DEL TEXTO */
    .stMarkdown p {
        font-size: 1.05rem !important;
        line-height: 1.7 !important;
        color: #e3e3e3 !important;
    }

    /* BARRA DE ENTRADA (CÁPSULA FLOTANTE) */
    [data-testid="stChatInput"] {
        position: fixed; bottom: 50px !important;
        left: 50% !important; transform: translateX(-50%) !important;
        width: 55% !important;
        background-color: #1e1f20 !important;
        border: 1px solid #3c3c3c !important;
        border-radius: 32px !important;
        padding: 10px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    [data-testid="stChatInput"] textarea { background-color: transparent !important; color: white !important; }
    
    /* BOTÓN ENVIAR BLANCO */
    [data-testid="stChatInput"] button { color: white !important; }

    /* DISCLAIMER */
    .custom-disclaimer {
        position: fixed; bottom: 15px; left: 0; right: 0;
        text-align: center; font-size: 0.75rem; color: #8e918f;
        z-index: 999;
    }

    /* BOTÓN LOGOUT (Top Right) */
    .logout-box { position: fixed; top: 15px; right: 20px; z-index: 1001; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGICA Y BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('linkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (session_id INTEGER, role TEXT, content TEXT)')
    conn.commit()
    conn.close()

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center; margin-top:30vh;'>🔗 Link AI</h2>", unsafe_allow_html=True)
    u = st.text_input("Usuario", placeholder="OmegaOne")
    p = st.text_input("Clave", type="password")
    if st.button("Ingresar"):
        # Lógica de login simplificada para el test
        st.session_state.logged_in = True
        st.session_state.username = u
        st.rerun()
    st.stop()

# --- 4. INTERFAZ ---
# Sidebar
with st.sidebar:
    st.button("☰", key="menu")
    if st.button("📝", key="new"):
        st.session_state.current_session_id = None
        st.rerun()

# Header superior
st.markdown(f"""
    <div class="top-nav">
        <div class="brand"><span>🔗</span> Link AI</div>
        <div class="chat-title">Nueva conversación</div>
    </div>
    <div class="logout-box"></div>
    """, unsafe_allow_html=True)

# Botón de cerrar sesión en la esquina
with st.container():
    col_l, col_r = st.columns([0.9, 0.1])
    with col_r:
        if st.button("Salir", key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()

# Cuerpo del chat
st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

if st.session_state.get("current_session_id"):
    conn = sqlite3.connect('linkai_pro.db')
    msgs = conn.execute("SELECT role, content FROM messages WHERE session_id=? ", (st.session_state.current_session_id,)).fetchall()
    for r, c in msgs:
        avatar = "🔗" if r == "assistant" else None
        with st.chat_message(r, avatar=avatar):
            st.markdown(c)
else:
    st.markdown(f"<h1 style='text-align:center; margin-top:20vh; font-weight:400; color:#e3e3e3;'>Hola, {st.session_state.username}</h1>", unsafe_allow_html=True)

# Disclaimer
st.markdown('<div class="custom-disclaimer">Link AI puede cometer errores, así que verifica sus respuestas.</div>', unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Escribe a Link AI..."):
    # Guardar y procesar (Lógica similar a la anterior...)
    pass
