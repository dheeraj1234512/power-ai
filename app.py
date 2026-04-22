import streamlit as st
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import hashlib
import extra_streamlit_components as stx

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

SHEET_ID = "1KZ4bnjGkOAjCy_vto-ESkcyl7LessM4IQmfMlSICFC0"

st.set_page_config(page_title="Power AI", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* ===== BACKGROUND ===== */
.stApp {
    background: linear-gradient(135deg, #020818 0%, #041530 30%, #020c20 60%, #010810 100%);
    min-height: 100vh;
}
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background:
        radial-gradient(ellipse at 20% 20%, rgba(0, 200, 255, 0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 80%, rgba(0, 100, 255, 0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(0, 150, 255, 0.04) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: rgba(4, 15, 40, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(0, 200, 255, 0.15) !important;
}
[data-testid="stSidebar"] * { color: #e2f0ff !important; }

/* ===== SIDEBAR TOGGLE FIX ===== */
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 50% !important;
    left: 0 !important;
    z-index: 99999 !important;
}
[data-testid="stSidebarCollapsedControl"] button {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    background: linear-gradient(135deg, #0066ff, #00ccff) !important;
    border: none !important;
    border-radius: 0 12px 12px 0 !important;
    width: 28px !important;
    height: 60px !important;
    box-shadow: 4px 0 20px rgba(0, 200, 255, 0.4) !important;
    cursor: pointer !important;
}
[data-testid="stSidebarCollapsedControl"] button svg {
    fill: white !important;
    color: white !important;
}
[data-testid="stSidebarCollapsedControl"] button:hover {
    background: linear-gradient(135deg, #0080ff, #00eeff) !important;
    box-shadow: 4px 0 30px rgba(0, 200, 255, 0.7) !important;
}

/* ===== HEADER ===== */
.main-header { text-align: center; padding: 20px 0 10px 0; }
.main-header h1 {
    font-family: 'Inter', sans-serif !important;
    font-size: 2.8em;
    font-weight: 800;
    background: linear-gradient(90deg, #00aaff, #00eeff, #0066ff, #00ccff);
    background-size: 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 4s ease infinite;
    letter-spacing: 4px;
    filter: drop-shadow(0 0 25px rgba(0, 200, 255, 0.6));
}
.main-header p {
    color: rgba(0, 200, 255, 0.7) !important;
    font-size: 0.85em;
    letter-spacing: 3px;
    text-transform: uppercase;
    font-weight: 400;
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ===== GLASSMORPHISM CARDS ===== */
.glass-card {
    background: rgba(0, 30, 80, 0.4) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(0, 200, 255, 0.2) !important;
    border-radius: 20px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.05) !important;
}

/* ===== CHAT MESSAGES ===== */
.stChatMessage[data-testid="stChatMessageUser"] {
    background: rgba(0, 100, 255, 0.2) !important;
    backdrop-filter: blur(15px) !important;
    -webkit-backdrop-filter: blur(15px) !important;
    border-radius: 20px 20px 5px 20px !important;
    border: 1px solid rgba(0, 180, 255, 0.35) !important;
    box-shadow: 0 8px 32px rgba(0, 100, 255, 0.2), inset 0 1px 0 rgba(255,255,255,0.08) !important;
    margin: 8px 0 !important;
    transition: all 0.3s ease !important;
}
.stChatMessage[data-testid="stChatMessageUser"]:hover {
    border-color: rgba(0, 200, 255, 0.6) !important;
    box-shadow: 0 12px 40px rgba(0, 150, 255, 0.3) !important;
    transform: translateY(-1px) !important;
}
.stChatMessage[data-testid="stChatMessageAssistant"] {
    background: rgba(0, 20, 60, 0.5) !important;
    backdrop-filter: blur(15px) !important;
    -webkit-backdrop-filter: blur(15px) !important;
    border-radius: 20px 20px 20px 5px !important;
    border: 1px solid rgba(0, 150, 255, 0.2) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(0, 200, 255, 0.05) !important;
    margin: 8px 0 !important;
    transition: all 0.3s ease !important;
}
.stChatMessage[data-testid="stChatMessageAssistant"]:hover {
    border-color: rgba(0, 200, 255, 0.4) !important;
    transform: translateY(-1px) !important;
}
.stChatMessage p, .stChatMessage div, .stChatMessage span {
    color: #e2f0ff !important;
    font-size: 1em !important;
    line-height: 1.7 !important;
    font-weight: 400 !important;
}

/* ===== CHAT INPUT ===== */
.stChatInput textarea {
    background: rgba(0, 20, 60, 0.6) !important;
    backdrop-filter: blur(20px) !important;
    color: #e2f0ff !important;
    border: 1px solid rgba(0, 150, 255, 0.4) !important;
    border-radius: 16px !important;
    font-size: 1em !important;
    font-weight: 400 !important;
    letter-spacing: 0.3px !important;
    padding: 14px 20px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.04) !important;
    transition: all 0.3s ease !important;
    caret-color: #00ccff !important;
    outline: none !important;
}
.stChatInput textarea:focus {
    border: 1px solid rgba(0, 200, 255, 0.7) !important;
    box-shadow: 0 0 0 3px rgba(0, 180, 255, 0.1), 0 0 25px rgba(0, 180, 255, 0.2) !important;
    outline: none !important;
}
.stChatInput textarea::placeholder { color: rgba(100, 180, 255, 0.35) !important; font-style: italic !important; }
.stChatInput button {
    background: linear-gradient(135deg, #0066ff, #00ccff) !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 15px rgba(0, 150, 255, 0.4) !important;
    transition: all 0.3s ease !important;
}
.stChatInput button:hover { transform: scale(1.08) !important; box-shadow: 0 6px 20px rgba(0, 200, 255, 0.6) !important; }
.stChatInput button svg { fill: white !important; }

/* ===== TEXT INPUT (LOGIN/REGISTER) ===== */
.stTextInput input {
    background: rgba(0, 20, 60, 0.5) !important;
    backdrop-filter: blur(10px) !important;
    color: #e2f0ff !important;
    border: 1px solid rgba(0, 150, 255, 0.3) !important;
    border-radius: 12px !important;
    font-size: 1em !important;
    font-weight: 400 !important;
    padding: 12px 16px !important;
    transition: all 0.3s ease !important;
    caret-color: #00ccff !important;
    outline: none !important;
}
.stTextInput input:focus {
    border: 1px solid rgba(0, 200, 255, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(0, 180, 255, 0.1), 0 0 20px rgba(0, 180, 255, 0.15) !important;
    outline: none !important;
    background: rgba(0, 25, 70, 0.6) !important;
}
.stTextInput input::placeholder { color: rgba(100, 180, 255, 0.35) !important; font-style: italic !important; }
.stTextInput input:focus-visible { outline: none !important; }
.stTextInput label {
    color: rgba(0, 200, 255, 0.8) !important;
    font-size: 0.8em !important;
    font-weight: 600 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

/* ===== BUTTONS ===== */
.stButton button {
    background: linear-gradient(135deg, #0055cc, #00aaff) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 15px rgba(0, 120, 255, 0.35) !important;
    transition: all 0.3s ease !important;
    font-size: 0.95em !important;
}
.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 150, 255, 0.5) !important;
    background: linear-gradient(135deg, #0066ff, #00ccff) !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(0, 20, 60, 0.4) !important;
    backdrop-filter: blur(10px) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid rgba(0, 150, 255, 0.15) !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    color: rgba(150, 200, 255, 0.7) !important;
    font-weight: 500 !important;
    font-size: 0.95em !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
    color: white !important;
    background: linear-gradient(135deg, #0055cc, #0099ee) !important;
    box-shadow: 0 2px 10px rgba(0, 120, 255, 0.3) !important;
}

/* ===== DIVIDER ===== */
hr {
    border-color: rgba(0, 150, 255, 0.15) !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: rgba(0, 10, 30, 0.5); }
::-webkit-scrollbar-thumb { background: linear-gradient(#0066ff, #00ccff); border-radius: 10px; }

/* ===== REMOVE OUTLINES ===== */
input, textarea, button, select { outline: none !important; -webkit-tap-highlight-color: transparent !important; }
input:focus, textarea:focus { outline: none !important; }
input:focus-visible, textarea:focus-visible { outline: none !important; }
*:focus { outline: none !important; }

/* ===== ALL TEXT ===== */
p, span, div, h1, h2, h3, label { color: #e2f0ff; }

#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===== COOKIE MANAGER =====
cookie_manager = stx.CookieManager()

def set_login_cookie(username):
    cookie_manager.set("power_ai_user", username, expires_at=datetime.now() + timedelta(days=7))

def get_login_cookie():
    return cookie_manager.get("power_ai_user")

def delete_login_cookie():
    cookie_manager.delete("power_ai_user")

# ===== GOOGLE SHEETS =====
def get_sheets():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        workbook = client.open_by_key(SHEET_ID)
        chat_sheet = workbook.sheet1
        users_sheet = workbook.worksheet("Users")
        return chat_sheet, users_sheet
    except Exception as e:
        st.error(f"Sheet Error: {e}")
        return None, None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    _, users_sheet = get_sheets()
    if users_sheet:
        users = users_sheet.get_all_records()
        for user in users:
            if user["Username"] == username:
                return False, "Username already exists!"
        users_sheet.append_row([username, hash_password(password), datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        return True, "Registration successful!"
    return False, "Sheet connect nahi hui!"

def login_user(username, password):
    _, users_sheet = get_sheets()
    if users_sheet:
        users = users_sheet.get_all_records()
        hashed = hash_password(password)
        for user in users:
            if user["Username"] == username and user["Password"] == hashed:
                return True
    return False

def save_chat(username, question, answer, chat_id):
    chat_sheet, _ = get_sheets()
    if chat_sheet:
        chat_sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), question, answer, username, chat_id])

def get_user_history(username):
    chat_sheet, _ = get_sheets()
    if chat_sheet:
        data = chat_sheet.get_all_records()
        return [row for row in data if row["Session ID"] == username]
    return []

# ===== SESSION STATE =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "is_guest" not in st.session_state:
    st.session_state.is_guest = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "store" not in st.session_state:
    st.session_state.store = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d%H%M%S")
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {}
if "reg_success" not in st.session_state:
    st.session_state.reg_success = False

# Cookie se login check
if not st.session_state.logged_in:
    saved_user = get_login_cookie()
    if saved_user and saved_user != "":
        st.session_state.logged_in = True
        st.session_state.username = saved_user
        st.session_state.is_guest = False
        history = get_user_history(saved_user)
        st.session_state.all_chats = {}
        for row in history:
            cid = row.get("Chat ID", "default")
            if cid not in st.session_state.all_chats:
                st.session_state.all_chats[cid] = []
            st.session_state.all_chats[cid].append({"role": "user", "content": row["User Question"]})
            st.session_state.all_chats[cid].append({"role": "assistant", "content": row["Bot Answer"]})
        st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.session_state.messages = []

# ===== LOGIN PAGE =====
if not st.session_state.logged_in:
    st.markdown("""
    <div class="main-header">
        <h1>⚡ POWER AI</h1>
        <p>Your Intelligent Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.reg_success:
            st.success("✅ Account ban gaya! Ab login karo!")

        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "👤 Guest"])

        with tab1:
            st.markdown("#### Welcome Back!")
            username = st.text_input("Username", key="login_user", placeholder="apna username likho")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="apna password likho")
            if st.button("Login ⚡", use_container_width=True, key="login_btn"):
                if username and password:
                    if login_user(username, password):
                        set_login_cookie(username)
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.is_guest = False
                        st.session_state.reg_success = False
                        st.session_state.messages = []
                        st.session_state.all_chats = {}
                        history = get_user_history(username)
                        for row in history:
                            cid = row.get("Chat ID", "default")
                            if cid not in st.session_state.all_chats:
                                st.session_state.all_chats[cid] = []
                            st.session_state.all_chats[cid].append({"role": "user", "content": row["User Question"]})
                            st.session_state.all_chats[cid].append({"role": "assistant", "content": row["Bot Answer"]})
                        st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        st.rerun()
                    else:
                        st.error("❌ Wrong username or password!")
                else:
                    st.warning("⚠️ Sab fields bharo!")

        with tab2:
            st.markdown("#### Create Account!")
            new_user = st.text_input("Username", key="reg_user", placeholder="naya username chuno")
            new_pass = st.text_input("Password", type="password", key="reg_pass", placeholder="strong password rakho")
            confirm_pass = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="password dobara likho")
            if st.button("Register ⚡", use_container_width=True, key="reg_btn"):
                if new_user and new_pass and confirm_pass:
                    if new_pass != confirm_pass:
                        st.error("❌ Passwords match nahi kar rahe!")
                    else:
                        success, msg = register_user(new_user, new_pass)
                        if success:
                            st.session_state.reg_success = True
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.warning("⚠️ Sab fields bharo!")

        with tab3:
            st.markdown("#### Guest Mode")
            st.info("⚠️ Guest mode mein chat history save nahi hogi!")
            if st.button("Guest ke taur pe continue karo 👤", use_container_width=True, key="guest_btn"):
                st.session_state.logged_in = True
                st.session_state.username = "Guest"
                st.session_state.is_guest = True
                st.session_state.messages = []
                st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d%H%M%S")
                st.rerun()

# ===== CHAT PAGE =====
else:
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 10px 0 20px 0;">
            <h2 style="font-family: Inter; font-size: 1.3em; font-weight: 800;
            background: linear-gradient(90deg, #00aaff, #00eeff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing: 3px;">⚡ POWER AI</h2>
        </div>
        """, unsafe_allow_html=True)

        if st.button("➕ New Chat", use_container_width=True):
            if st.session_state.messages:
                st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()
            new_id = datetime.now().strftime("%Y%m%d%H%M%S")
            st.session_state.current_chat_id = new_id
            st.session_state.messages = []
            st.session_state.store = {}
            st.rerun()

        st.divider()

        if not st.session_state.is_guest and st.session_state.all_chats:
            st.markdown("<p style='font-size:0.8em; color: rgba(0,200,255,0.6); letter-spacing:1px; text-transform:uppercase; font-weight:600;'>Recent Chats</p>", unsafe_allow_html=True)
            for chat_id, chat_msgs in reversed(list(st.session_state.all_chats.items())):
                if chat_msgs:
                    first_q = chat_msgs[0]["content"][:28] + "..." if len(chat_msgs[0]["content"]) > 28 else chat_msgs[0]["content"]
                    is_active = chat_id == st.session_state.current_chat_id
                    border_color = "rgba(0, 200, 255, 0.6)" if is_active else "rgba(0, 100, 255, 0.2)"
                    bg_color = "rgba(0, 100, 255, 0.2)" if is_active else "rgba(0, 30, 80, 0.3)"
                    st.markdown(f"""
                    <div style="background:{bg_color}; border:1px solid {border_color};
                    border-radius:10px; padding:10px 12px; margin:4px 0;
                    font-size:0.85em; color:#c0d8ff; cursor:pointer;
                    backdrop-filter:blur(10px);">
                        💬 {first_q}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Open", key=f"chat_{chat_id}"):
                        if st.session_state.messages:
                            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()
                        st.session_state.current_chat_id = chat_id
                        st.session_state.messages = chat_msgs.copy()
                        st.session_state.store = {}
                        st.rerun()

        st.divider()

        if st.session_state.is_guest:
            st.markdown("<p style='font-size:0.9em;'>👤 Guest Mode</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size:0.9em;'>👤 <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)

        if st.button("🚪 Logout", use_container_width=True):
            delete_login_cookie()
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.is_guest = False
            st.session_state.messages = []
            st.session_state.store = {}
            st.session_state.all_chats = {}
            st.session_state.reg_success = False
            st.rerun()

    # ===== MAIN CHAT =====
    st.markdown("""
    <div class="main-header">
        <h1>⚡ POWER AI</h1>
        <p>Your Intelligent Assistant — Hindi & English</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Tum Power AI ho — ek powerful aur helpful AI assistant. User ka naam {st.session_state.username} hai. Hindi aur English dono mein baat kar sakte ho. Hamesha polite aur helpful raho."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    chain = prompt | llm

    def get_session_history(session_id: str):
        if session_id not in st.session_state.store:
            st.session_state.store[session_id] = ChatMessageHistory()
        return st.session_state.store[session_id]

    chatbot = RunnableWithMessageHistory(
        chain, get_session_history,
        input_messages_key="input",
        history_messages_key="history"
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("⚡ Ask Anything To Power AI...")

    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("⚡ Thinking..."):
            response = chatbot.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": st.session_state.current_chat_id}}
            )

        bot_reply = response.content
        with st.chat_message("assistant"):
            st.write(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        if not st.session_state.is_guest:
            save_chat(st.session_state.username, user_input, bot_reply, st.session_state.current_chat_id)
            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()