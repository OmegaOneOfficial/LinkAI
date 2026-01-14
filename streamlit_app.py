import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime

# Manejo de PDF
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# --- 1. CONFIGURACIÓN Y UI ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #09090b; color: #fafafa; }
    
    /* Burbujas de chat ultra-redondeadas */
    div.stChatMessage {
        border-radius: 25px !important;
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        margin-bottom: 20px;
    }

    /* Estilo de la barra de entrada con el botón + */
    .stChatInputContainer {
        padding-bottom: 20px;
    }
    
    /* Sidebar moderna */
    [data-testid="stSidebar"] {
        background-color: #09090b !important;
        border-right: 1px solid #27272a !important;
    }

    .main-title {
        font-size: 3rem; font-weight: 900; text-align: center;
        background: linear-gradient(to right, #fff, #4facfe);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }

    /* Ocultar el label del uploader para que no ensucie la UI */
    .stFileUploader label { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('linkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT, created_at DATETIME)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (session_id INTEGER, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    conn.close()

init_db()

# --- 3. GESTIÓN DE SESIÓN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>Link AI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        m = st.tabs(["Login", "Registro"])
        with m[0]:
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.button("Entrar", use_container_width=True):
                conn = sqlite3.connect('linkai_pro.db')
                res = conn.execute("SELECT password FROM users WHERE username=?", (u,)).fetchone()
                if res and hashlib.sha256(p.encode()).hexdigest() == res[0]:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else: st.error("Fallo de acceso")
        with m[1]:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Clave", type="password")
            if st.button("Registrar", use_container_width=True):
                conn = sqlite3.connect('linkai_pro.db')
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?)", (nu, hashlib.sha256(np.encode()).hexdigest(), "user"))
                    conn.commit()
                    st.success("¡Listo!")
                except: st.error("Ya existe")
    st.stop()

# --- 4. CONFIGURACIÓN IA (AUTO-DETECCIÓN) ---
genai.configure(api_key="AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug")

@st.cache_resource
def get_model():
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target = next((m for m in models if 'gemini-1.5-flash' in m), models[0])
    return genai.GenerativeModel(
        model_name=target,
        system_instruction=f"Soy Link AI impulsada por OmegaOne. Usuario: {st.session_state.username}. Responde siempre en español.",
        safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
    )

model = get_model()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.username}")
    if st.button("＋ Nuevo Chat", use_container_width=True):
        st.session_state.current_session_id = None
        st.rerun()
    st.markdown("---")
    conn = sqlite3.connect('linkai_pro.db')
    chats = conn.execute("SELECT id, title FROM chat_sessions WHERE username=? ORDER BY created_at DESC LIMIT 8", (st.session_state.username,)).fetchall()
    for cid, title in chats:
        if st.button(f"💬 {title[:15]}...", key=f"c_{cid}", use_container_width=True):
            st.session_state.current_session_id = cid
            st.rerun()
    if st.button("Salir"):
        st.session_state.logged_in = False
        st.rerun()

# --- 6. CHAT Y ARCHIVOS ---
st.markdown("<h1 style='text-align:center;'>Link AI</h1>", unsafe_allow_html=True)

# El "botón +" integrado arriba de la barra de chat
col_file, col_txt = st.columns([0.1, 0.9])
with col_file:
    uploaded_file = st.file_uploader("＋", type=['pdf', 'txt'], label_visibility="collapsed")

if st.session_state.get("current_session_id"):
    conn = sqlite3.connect('linkai_pro.db')
    msgs = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC", (st.session_state.current_session_id,)).fetchall()
    for r, c in msgs:
        with st.chat_message(r): st.markdown(c)

if prompt := st.chat_input("Escribe tu mensaje..."):
    conn = sqlite3.connect('linkai_pro.db')
    if not st.session_state.get("current_session_id"):
        cursor = conn.execute("INSERT INTO chat_sessions (username, title, created_at) VALUES (?,?,?)", (st.session_state.username, prompt[:20], datetime.now()))
        st.session_state.current_session_id = cursor.lastrowid
        conn.commit()

    full_context = prompt
    if uploaded_file:
        st.toast(f"Analizando {uploaded_file.name}...")
        if uploaded_file.type == "application/pdf" and PyPDF2:
            reader = PyPDF2.PdfReader(uploaded_file)
            txt = "".join([p.extract_text() for p in reader.pages])
            full_context += f"\n\n[ARCHIVO]: {txt}"
        else:
            full_context += f"\n\n[ARCHIVO]: {str(uploaded_file.read(), 'utf-8')}"

    with st.chat_message("user"): st.markdown(prompt)
    conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "user", prompt, datetime.now()))
    conn.commit()

    with st.chat_message("assistant"):
        ph = st.empty()
        res = ""
        try:
            response = model.generate_content(full_context, stream=True)
            for chunk in response:
                if chunk.text:
                    res += chunk.text
                    ph.markdown(res + "▌")
            ph.markdown(res)
            conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "assistant", res, datetime.now()))
            conn.commit()
        except Exception as e:
            st.error("Error de conexión. Intenta de nuevo.")
