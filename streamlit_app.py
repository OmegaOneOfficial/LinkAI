import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

# --- 2. CSS PARA IMITAR LA UI DE GEMINI ---
st.markdown("""
    <style>
    /* Fondo Gris Oscuro / Negro */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
    }

    /* Ocultar elementos nativos de Streamlit */
    header, footer, #MainMenu {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}

    /* BARRA SUPERIOR */
    .header-container {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 20px;
        background-color: #121212;
        z-index: 1000;
    }
    .brand-left {
        font-size: 1.2rem;
        font-weight: 600;
        color: #FFFFFF;
    }
    .chat-title-center {
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        color: #AAAAAA;
        font-size: 0.9rem;
    }

    /* BOTÓN LOGOUT (Top Right) */
    .stButton>button[key="logout_btn"] {
        background-color: transparent !important;
        border: 1px solid #444 !important;
        color: white !important;
        border-radius: 20px !important;
        padding: 2px 15px !important;
    }

    /* SIDEBAR CHIQUITA */
    [data-testid="stSidebar"] {
        width: 80px !important;
        background-color: #0F0F0F !important;
        border-right: none !important;
    }
    /* Botones Sidebar Cuadrados y Transparentes */
    .stButton>button[key="new_chat_btn"], .stButton>button[key="list_chats_btn"] {
        background-color: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 1.5rem !important;
        width: 50px !important;
        height: 50px !important;
        margin: 10px auto !important;
        display: block !important;
    }

    /* TEXTO SIN RECUADROS */
    div.stChatMessage {
        background-color: transparent !important;
        border: none !important;
        color: white !important;
        margin-bottom: 5px;
        padding: 0px 10% !important;
    }
    
    /* BARRA DE ESCRITURA FLOTANTE */
    .stChatInput {
        position: fixed;
        bottom: 50px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 60% !important;
        background-color: #282828 !important; /* Gris */
        border-radius: 30px !important;
        border: 1px solid #3c3c3c !important;
        z-index: 999;
    }
    .stChatInput textarea {
        background-color: transparent !important;
        color: white !important;
    }
    .stChatInput button {
        background-color: transparent !important;
        color: white !important;
    }

    /* TEXTO INFERIOR DE ADVERTENCIA */
    .disclaimer {
        position: fixed;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.75rem;
        color: #777;
        text-align: center;
        width: 100%;
    }
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
    st.markdown("<h1 style='text-align:center; margin-top:15vh;'>Link AI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Log In", use_container_width=True):
            conn = sqlite3.connect('linkai_pro.db')
            res = conn.execute("SELECT password FROM users WHERE username=?", (u,)).fetchone()
            if res and hashlib.sha256(p.encode()).hexdigest() == res[0]:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
    st.stop()

# --- HEADER (Link AI, Título Chat, Logout) ---
current_title = "Nueva conversación"
if st.session_state.get("current_session_id"):
    conn = sqlite3.connect('linkai_pro.db')
    res = conn.execute("SELECT title FROM chat_sessions WHERE id=?", (st.session_state.current_session_id,)).fetchone()
    if res: current_title = res[0]

st.markdown(f"""
    <div class="header-container">
        <div class="brand-left">Link AI</div>
        <div class="chat-title-center">{current_title}</div>
        <div></div> </div>
    """, unsafe_allow_html=True)

# Botón Logout flotando a la derecha
with st.container():
    col_empty, col_btn = st.columns([0.9, 0.1])
    with col_btn:
        if st.button("Log Out", key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()

# --- 5. SIDEBAR (Solo Iconos Cuadrados) ---
with st.sidebar:
    # Botón Nuevo Chat (Cuadrado y Transparente)
    if st.button("＋", key="new_chat_btn", help="Nuevo Chat"):
        st.session_state.current_session_id = None
        st.rerun()
    
    # Botón Lista de Chats (3 líneas / menú)
    show_list = st.toggle("☰", key="list_chats_btn", label_visibility="collapsed")
    
    if show_list:
        st.markdown("---")
        conn = sqlite3.connect('linkai_pro.db')
        chats = conn.execute("SELECT id, title FROM chat_sessions WHERE username=? ORDER BY created_at DESC LIMIT 8", (st.session_state.username,)).fetchall()
        for cid, title in chats:
            if st.button(f"{title[:15]}", key=f"c_{cid}", use_container_width=True):
                st.session_state.current_session_id = cid
                st.rerun()

# --- 6. CHAT ---
st.markdown("<br><br>", unsafe_allow_html=True) # Espacio para el header

if st.session_state.get("current_session_id"):
    conn = sqlite3.connect('linkai_pro.db')
    msgs = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC", (st.session_state.current_session_id,)).fetchall()
    for r, c in msgs:
        with st.chat_message(r):
            st.markdown(c)

# DISCLAIMER INFERIOR
st.markdown('<div class="disclaimer">Link AI puede cometer errores, así que verifica sus respuestas.</div>', unsafe_allow_html=True)

# INPUT FLOTANTE
if prompt := st.chat_input("Escribe tu mensaje..."):
    conn = sqlite3.connect('linkai_pro.db')
    if not st.session_state.get("current_session_id"):
        cursor = conn.execute("INSERT INTO chat_sessions (username, title, created_at) VALUES (?,?,?)", (st.session_state.username, prompt[:25], datetime.now()))
        st.session_state.current_session_id = cursor.lastrowid
        conn.commit()

    with st.chat_message("user"): st.markdown(prompt)
    conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "user", prompt, datetime.now()))
    conn.commit()

    # RESPUESTA IA
    genai.configure(api_key="AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug")
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    
    with st.chat_message("assistant"):
        ph = st.empty()
        full_res = ""
        try:
            # Ventana de contexto corta
            hist_db = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC LIMIT 6", (st.session_state.current_session_id,)).fetchall()
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
        except:
            st.error("Error.")
