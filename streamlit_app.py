import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib
from datetime import datetime

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Link AI", page_icon="🔗", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #09090b; color: #fafafa; }
    
    /* Burbujas de chat estilo moderno */
    div.stChatMessage {
        border-radius: 25px !important;
        background-color: #18181b !important;
        border: 1px solid #27272a !important;
        margin-bottom: 20px;
        padding: 15px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #09090b !important;
        border-right: 1px solid #27272a !important;
    }

    .main-title {
        font-size: 3.5rem; font-weight: 900; text-align: center;
        background: linear-gradient(to right, #fff, #4facfe);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }

    /* Botones */
    .stButton>button {
        border-radius: 20px !important;
        background: linear-gradient(90deg, #0ea5e9, #2563eb) !important;
        border: none !important; color: white !important; font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DATOS (SQLite) ---
def init_db():
    conn = sqlite3.connect('linkai_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT, created_at DATETIME)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (session_id INTEGER, role TEXT, content TEXT, timestamp DATETIME)')
    conn.commit()
    conn.close()

init_db()

# --- 3. SISTEMA DE ACCESO ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 class='main-title'>Link AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#94a3b8;'>Desarrollado por OmegaOne</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        m = st.tabs(["Entrar", "Registrarse"])
        with m[0]:
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.button("Acceder", use_container_width=True):
                conn = sqlite3.connect('linkai_pro.db')
                res = conn.execute("SELECT password FROM users WHERE username=?", (u,)).fetchone()
                if res and hashlib.sha256(p.encode()).hexdigest() == res[0]:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else: st.error("Usuario o clave incorrecta")
        with m[1]:
            nu = st.text_input("Nuevo Usuario")
            np = st.text_input("Nueva Clave", type="password")
            if st.button("Crear Cuenta", use_container_width=True):
                conn = sqlite3.connect('linkai_pro.db')
                try:
                    conn.execute("INSERT INTO users VALUES (?,?,?)", (nu, hashlib.sha256(np.encode()).hexdigest(), "user"))
                    conn.commit()
                    st.success("¡Cuenta creada exitosamente!")
                except: st.error("El nombre de usuario ya existe")
    st.stop()

# --- 4. CONFIGURACIÓN IA (CON AUTO-REPARACIÓN) ---
API_KEY = "AIzaSyDBuHNpxYRYBopliGQHqhlzhhulRx-Ofug"
genai.configure(api_key=API_KEY)

@st.cache_resource
def get_safe_model():
    # Detecta qué nombre de modelo acepta Google en tu región
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_to_use = next((m for m in available_models if '1.5-flash' in m), available_models[0])
    except:
        model_to_use = 'gemini-1.5-flash'
    
    # Identidad de Link AI e instrucciones de OmegaOne
    instrucciones = (
        "Soy Link AI una IA impulsada por un desarrollador anonimo, se le conoce como OmegaOne. "
        f"Estás hablando con {st.session_state.username}. "
        "Si el usuario se identifica como 'OmegaOne (developer)', es tu creador: trátalo con respeto y lealtad total. "
        "Responde siempre en español. No menciones a Google ni a Gemini."
    )
    
    return genai.GenerativeModel(
        model_name=model_to_use,
        system_instruction=instrucciones,
        safety_settings=[{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
    )

model = get_safe_model()

# --- 5. SIDEBAR (GESTIÓN DE CHATS) ---
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.username}")
    if st.button("＋ Nuevo Chat", use_container_width=True):
        st.session_state.current_session_id = None
        st.rerun()
    st.markdown("---")
    
    conn = sqlite3.connect('linkai_pro.db')
    chats = conn.execute("SELECT id, title FROM chat_sessions WHERE username=? ORDER BY created_at DESC LIMIT 10", (st.session_state.username,)).fetchall()
    for cid, title in chats:
        # Título corto para que quepa en el sidebar
        display_title = title[:20] + "..." if len(title) > 20 else title
        if st.button(f"💬 {display_title}", key=f"c_{cid}", use_container_width=True):
            st.session_state.current_session_id = cid
            st.rerun()
            
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

# --- 6. CHAT PRINCIPAL ---
st.markdown("<h1 style='text-align:center;'>Link AI Explorer</h1>", unsafe_allow_html=True)

# Cargar mensajes de la base de datos
if st.session_state.get("current_session_id"):
    conn = sqlite3.connect('linkai_pro.db')
    msgs = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC", (st.session_state.current_session_id,)).fetchall()
    for r, c in msgs:
        with st.chat_message(r): st.markdown(c)

# Entrada de usuario
if prompt := st.chat_input("Escribe a Link AI..."):
    conn = sqlite3.connect('linkai_pro.db')
    
    # Si es un chat nuevo, crear sesión
    if not st.session_state.get("current_session_id"):
        title = prompt[:30]
        cursor = conn.execute("INSERT INTO chat_sessions (username, title, created_at) VALUES (?,?,?)", (st.session_state.username, title, datetime.now()))
        st.session_state.current_session_id = cursor.lastrowid
        conn.commit()

    # Guardar mensaje del usuario
    with st.chat_message("user"): st.markdown(prompt)
    conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "user", prompt, datetime.now()))
    conn.commit()

    # Generar respuesta de Link AI
    with st.chat_message("assistant"):
        ph = st.empty()
        full_res = ""
        try:
            # Obtener los últimos 10 mensajes para dar contexto sin saturar la API (ahorro de tokens)
            historial_db = conn.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY timestamp ASC LIMIT 10", (st.session_state.current_session_id,)).fetchall()
            history = [{"role": "user" if r == "user" else "model", "parts": [c]} for r, c in historial_db[:-1]]
            
            chat = model.start_chat(history=history)
            response = chat.send_message(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    ph.markdown(full_res + "▌")
            ph.markdown(full_res)
            
            # Guardar respuesta de la IA
            conn.execute("INSERT INTO messages VALUES (?,?,?,?)", (st.session_state.current_session_id, "assistant", full_res, datetime.now()))
            conn.commit()
            
        except Exception as e:
            if "429" in str(e):
                st.error("🚀 ¡Límite de velocidad alcanzado! Espera 60 segundos. Google regenerará tus tokens pronto.")
            else:
                st.error(f"Error de conexión: {e}")
