import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

# --- 2. CSS DE PRECISIÓN (ESTILO LINK AI) ---
st.markdown("""
    <style>
    /* Fondo y Tipografía */
    .stApp {
        background-color: #131314;
        color: #e3e3e3;
        font-family: 'Google Sans', Arial, sans-serif;
    }

    /* Ocultar elementos nativos */
    header, footer, #MainMenu {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}

    /* BARRA SUPERIOR */
    .top-nav {
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 64px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 20px;
        background-color: #131314;
        z-index: 1000;
    }
    .brand-container { display: flex; align-items: center; gap: 10px; }
    .brand-text { font-size: 1.4rem; font-weight: 500; color: #e3e3e3; }
    .chat-name { color: #c4c7c5; font-size: 0.9rem; position: absolute; left: 50%; transform: translateX(-50%); }

    /* BOTONES SIDEBAR (TRANSPARENTES Y CUADRADOS) */
    [data-testid="stSidebar"] {
        width: 70px !important;
        background-color: #1e1f20 !important;
        border: none !important;
    }
    .stButton>button[key="menu_btn"], .stButton>button[key="new_btn"] {
        background-color: transparent !important;
        border: none !important;
        color: #e3e3e3 !important;
        font-size: 1.4rem !important;
        height: 48px !important;
        width: 48px !important;
        margin-bottom: 10px !important;
        display: flex;
        justify-content: center;
    }

    /* MENSAJES SIN RECUADROS */
    div.stChatMessage {
        background-color: transparent !important;
        border: none !important;
        padding: 10px 18% !important;
    }
    
    /* Icono de Link AI en el chat */
    .stChatMessage [data-testid="stChatAvatar"] {
        background-color: transparent !important;
    }

    /* CAJA DE TEXTO FLOTANTE */
    .stChatInput {
        position: fixed;
        bottom: 60px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 55% !important;
        background-color: #1e1f20 !important;
        border-radius: 28px !important;
        border: none !important;
    }
    .stChatInput textarea { color: #e3e3e3 !important; }
    
    /* BOTÓN ENVIAR BLANCO */
    .stChatInput button svg { fill: #ffffff !important; }

    /* DISCLAIMER INFERIOR PERSONALIZADO */
    .footer-disclaimer {
        position: fixed;
        bottom: 15px;
        left: 0; right: 0;
        text-align: center;
        font-size: 0.75rem;
        color: #8e918f;
    }

    /* BOTÓN CERRAR SESIÓN */
    .stButton>button[key="logout"] {
        background-color: #1e1f20 !important;
        border: 1px solid #333 !important;
        color: white !important;
        border-radius: 20px !important;
        font-size: 0.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BASE DE DATOS Y SESIÓN ---
def init_db():
    conn = sqlite3.connect('linkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT, created_at DATETIME)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (session_id INTEGER, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    conn.close()

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center; margin-top:20vh;'>🔗 Link AI</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        u = st.text_input("Usuario")
        p = st.text_input("Clave", type="password")
        if st.button("Entrar", use_container_width=True):
            conn = sqlite3.connect('linkai_pro.db')
            res = conn.execute("SELECT password FROM users WHERE username=?", (u,)).fetchone()
            if res and hashlib.sha256(p.encode()).hexdigest() == res[0]:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
    st.stop()

# --- 4. CABECERA Y SIDEBAR ---
with st.sidebar:
    st.button("☰", key="menu_btn")
    if st.button("＋", key="new_btn"):
        st.session_state.current_session_id = None
        st.rerun()

# Header
title_chat = "Nueva conversación"
if st.session_state.get("current_session_id"):
    conn = sqlite3.connect('linkai_pro.db')
    res = conn.execute("SELECT title FROM chat_sessions WHERE id=?", (st.session_state.current_session_id,)).fetchone()
    if res: title_chat = res[0]

st.markdown(f"""
    <div class="top-nav">
        <div class="brand-container">
            <span style="font-size:1.5rem;">🔗</span>
            <span class="brand-text">Link AI</span>
        </div>
        <div class="chat-name">{title_chat}</div>
        <div></div>
    </div>
    """, unsafe_allow_html=True)

# Logout
t1, t2 = st.columns([0.92, 0.08])
with t2:
    if st.button("Log Out", key="logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 5. CUERPO DEL CHAT ---
st.markdown("<div style='margin-top:70px;'></div>", unsafe_allow_html=True)

if st.session_state.get("current_session_id"):
    conn = sqlite3.connect('linkai_pro.db')
    msgs = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC", (st.session_state.current_session_id,)).fetchall()
    for r, c in msgs:
        # Usamos el logo 🔗 para la IA
        avatar = "🔗" if r == "assistant" else None
        with st.chat_message(r, avatar=avatar):
            st.markdown(c)
else:
    st.markdown(f"""
        <div style='text-align:center; margin-top:15vh;'>
            <h1 style='color:#e3e3e3; font-weight:400;'>Hola, {st.session_state.username}</h1>
            <p style='color:#8e918f;'>¿En qué puedo apoyarte hoy con Link AI?</p>
        </div>
    """, unsafe_allow_html=True)

# Disclaimer Inferior
st.markdown('<div class="footer-disclaimer">Link AI puede cometer errores, así que verifica sus respuestas.</div>', unsafe_allow_html=True)

# --- 6. LÓGICA DE IA ---
if prompt := st.chat_input("Pregunta a Link AI"):
    conn = sqlite3.connect('linkai_pro.db')
    if not st.session_state.get("current_session_id"):
        cursor = conn.execute("INSERT INTO chat_sessions (username, title, created_at) VALUES (?,?,?)", (st.session_state.username, prompt[:30], datetime.now()))
        st.session_state.current_session_id = cursor.lastrowid
        conn.commit()

    conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "user", prompt, datetime.now()))
    conn.commit()
    
    # Generación de respuesta (Gemini Flash bajo el nombre Link AI)
    genai.configure(api_key="AIZA...") # Usa tu clave aquí
    model = genai.GenerativeModel(
        model_name='models/gemini-1.5-flash',
        system_instruction="Soy Link AI una IA impulsada por un desarrollador anonimo, se le conoce como OmegaOne."
    )
    
    with st.chat_message("assistant", avatar="🔗"):
        ph = st.empty()
        full_res = ""
        # Simulamos streaming
        response = model.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                full_res += chunk.text
                ph.markdown(full_res + "▌")
        ph.markdown(full_res)
        conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "assistant", full_res, datetime.now()))
        conn.commit()
