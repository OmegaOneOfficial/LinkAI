import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime
import PyPDF2 # Necesitas poner 'PyPDF2' en requirements.txt

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

# --- 2. UI ULTRA PREMIUM (CSS CUSTOM) ---
st.markdown("""
    <style>
    /* Fondo con gradiente sutil y desenfoque */
    .stApp {
        background: radial-gradient(circle at top right, #1e1e2f, #0f0f13);
        color: #e0e0e0;
    }
    
    /* Contenedores con bordes redondeados y efecto Glassmorphism */
    div.stChatMessage {
        border-radius: 20px !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        margin-bottom: 15px;
        padding: 15px;
    }
    
    /* Barra lateral estilizada */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 10, 15, 0.95) !important;
        border-right: 1px solid #2d2d3d !important;
    }

    /* Botones Neón */
    .stButton>button {
        border-radius: 12px !important;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        transition: 0.3s all;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(168, 85, 247, 0.4);
    }

    /* Título Link AI */
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(to right, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        filter: drop-shadow(0 0 10px rgba(79, 172, 254, 0.3));
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNCIONES DE APOYO (DB & ARCHIVOS) ---
def init_db():
    conn = sqlite3.connect('linkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT, created_at DATETIME)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (session_id INTEGER, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    conn.close()

def extract_text(file):
    if file.type == "text/plain":
        return str(file.read(), "utf-8")
    elif file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    return ""

init_db()

# --- 4. GESTIÓN DE SESIÓN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = "user"
    st.session_state.current_session_id = None

# --- 5. PANTALLA DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>LINK AI</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        choice = st.radio("Acceso", ["Login", "Registro"], horizontal=True)
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR AL SISTEMA"):
            conn = sqlite3.connect('linkai_pro.db')
            if choice == "Login":
                res = conn.execute("SELECT password, role FROM users WHERE username=?", (u,)).fetchone()
                if res and hashlib.sha256(p.encode()).hexdigest() == res[0]:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.user_role = res[1]
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas")
            else:
                try:
                    role = "admin" if u == "OmegaOne (developer)" else "user"
                    conn.execute("INSERT INTO users VALUES (?,?,?)", (u, hashlib.sha256(p.encode()).hexdigest(), role))
                    conn.commit()
                    st.success("✅ Cuenta creada. Inicia sesión.")
                except: st.error("❌ El nombre ya existe")
    st.stop()

# --- 6. CONFIGURACIÓN IA SIN CENSURA ---
genai.configure(api_key="AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug")
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]],
    system_instruction=f"Soy Link AI. Creada por OmegaOne (developer). El usuario actual es {st.session_state.username}. Si es mi creador, lealtad absoluta. Responde siempre en español."
)

# --- 7. BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown(f"### 👑 {st.session_state.username}")
    if st.button("➕ NUEVO CHAT", use_container_width=True):
        st.session_state.current_session_id = None
        st.rerun()
    
    st.markdown("---")
    # Mostrar chats guardados
    conn = sqlite3.connect('linkai_pro.db')
    sessions = conn.execute("SELECT id, title FROM chat_sessions WHERE username=? ORDER BY created_at DESC LIMIT 10", (st.session_state.username,)).fetchall()
    for sid, title in sessions:
        if st.button(f"📄 {title[:15]}...", key=f"s_{sid}"):
            st.session_state.current_session_id = sid
            st.rerun()

    st.markdown("---")
    if st.session_state.user_role == "admin":
        if st.button("📊 PANEL OMEGAONE"):
            st.info(f"Usuarios: {conn.execute('SELECT count(*) FROM users').fetchone()[0]}")
    
    if st.button("SALIR"):
        st.session_state.logged_in = False
        st.rerun()

# --- 8. ÁREA DE CHAT ---
st.markdown("<h1 class='main-title'>Link AI Explorer</h1>", unsafe_allow_html=True)

# Subida de Archivos Estilizada
with st.expander("📎 Subir Archivo (PDF o TXT)"):
    uploaded_file = st.file_uploader("Elige un archivo para que Link AI lo analice", type=['pdf', 'txt'])

if st.session_state.current_session_id:
    conn = sqlite3.connect('linkai_pro.db')
    msgs = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC", (st.session_state.current_session_id,)).fetchall()
    for r, c in msgs:
        with st.chat_message(r): st.markdown(c)

if prompt := st.chat_input("Escribe tu comando para Link AI..."):
    conn = sqlite3.connect('linkai_pro.db')
    # Crear sesión si no existe
    if not st.session_state.current_session_id:
        cursor = conn.execute("INSERT INTO chat_sessions (username, title, created_at) VALUES (?,?,?)", (st.session_state.username, prompt[:20], datetime.now()))
        st.session_state.current_session_id = cursor.lastrowid
        conn.commit()

    # Si hay archivo, leerlo
    contexto_archivo = ""
    if uploaded_file:
        contexto_archivo = f"\n\n[CONTEXTO DEL ARCHIVO]:\n{extract_text(uploaded_file)}"

    # Guardar y mostrar
    with st.chat_message("user"): st.markdown(prompt)
    conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "user", prompt, datetime.now()))
    conn.commit()

    with st.chat_message("assistant"):
        ph = st.empty()
        full_res = ""
        # Chat con la IA enviando el prompt + el texto del archivo
        response = model.generate_content(prompt + contexto_archivo, stream=True)
        for chunk in response:
            if chunk.text:
                full_res += chunk.text
                ph.markdown(full_res + "▌")
        ph.markdown(full_res)
        conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "assistant", full_res, datetime.now()))
        conn.commit()
