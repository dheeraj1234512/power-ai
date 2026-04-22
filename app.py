import streamlit as st
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import hashlib

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

st.set_page_config(page_title="Power AI", page_icon="⚡", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');
.stApp {
    background: radial-gradient(ellipse at top, #1a0a2e 0%, #0a0a0a 50%, #0d0015 100%);
    font-family: 'Rajdhani', sans-serif;
}
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image: 
        linear-gradient(rgba(123, 47, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(123, 47, 255, 0.05) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
}
.main-header { text-align: center; padding: 30px 0 10px 0; }
.main-header h1 {
    font-family: 'Orbitron', sans-serif;
    font-size: 3.5em;
    font-weight: 900;
    background: linear-gradient(90deg, #7b2fff, #ff2fff, #00d4ff, #7b2fff);
    background-size: 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 4s ease infinite;
    letter-spacing: 5px;
    filter: drop-shadow(0 0 20px rgba(123, 47, 255, 0.8));
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.main-header p { color: #a78bfa !important; font-size: 1em; letter-spacing: 3px; text-transform: uppercase; }
.stChatMessage[data-testid="stChatMessageUser"] {
    background: linear-gradient(135deg, #2d1b69 0%, #7b2fff 100%) !important;
    border-radius: 20px 20px 5px 20px !important;
    border: 1px solid rgba(123, 47, 255, 0.8) !important;
    box-shadow: 0 8px 32px rgba(123, 47, 255, 0.4), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    transform: perspective(1000px) rotateX(1deg);
    transition: all 0.3s ease !important;
    margin: 8px 0 !important;
}
.stChatMessage[data-testid="stChatMessageUser"]:hover {
    transform: perspective(1000px) rotateX(0deg) translateY(-2px);
    box-shadow: 0 15px 40px rgba(123, 47, 255, 0.6) !important;
}
.stChatMessage[data-testid="stChatMessageAssistant"] {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%) !important;
    border-radius: 20px 20px 20px 5px !important;
    border: 1px solid rgba(123, 47, 255, 0.4) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(123, 47, 255, 0.1) !important;
    transform: perspective(1000px) rotateX(-1deg);
    transition: all 0.3s ease !important;
    margin: 8px 0 !important;
}
.stChatMessage[data-testid="stChatMessageAssistant"]:hover {
    transform: perspective(1000px) rotateX(0deg) translateY(-2px);
}
.stChatMessage p, .stChatMessage div { color: #e2d9f3 !important; font-size: 1.05em !important; line-height: 1.6 !important; }
.stChatInput textarea {
    background: linear-gradient(145deg, #120826, #1e0d3a) !important;
    color: #f0e6ff !important;
    border: 1.5px solid rgba(180, 120, 255, 0.5) !important;
    border-radius: 18px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.2em !important;
    font-weight: 500 !important;
    letter-spacing: 0.8px !important;
    padding: 14px 20px !important;
    box-shadow: 0 4px 30px rgba(100, 30, 200, 0.25), inset 0 2px 12px rgba(0,0,0,0.6) !important;
    transition: all 0.4s ease !important;
    caret-color: #c084fc !important;
    outline: none !important;
}
.stChatInput textarea:focus {
    border: 1.5px solid rgba(192, 132, 252, 0.9) !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15), 0 0 30px rgba(139, 92, 246, 0.4) !important;
    outline: none !important;
}
.stChatInput textarea::placeholder { color: rgba(167, 139, 250, 0.4) !important; font-style: italic !important; }
.stChatInput button { background: linear-gradient(135deg, #7b2fff, #ff2fff) !important; border: none !important; border-radius: 10px !important; box-shadow: 0 4px 15px rgba(123, 47, 255, 0.5) !important; transition: all 0.3s ease !important; }
.stChatInput button:hover { transform: scale(1.1) !important; box-shadow: 0 8px 25px rgba(123, 47, 255, 0.8) !important; }
.stChatInput button svg { fill: white !important; }
*:focus { outline: none !important; }
*:focus-visible { outline: 2px solid rgba(139, 92, 246, 0.5) !important; outline-offset: 2px !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: linear-gradient(#7b2fff, #ff2fff); border-radius: 10px; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

/* Login Form Styling */
.login-box {
    background: linear-gradient(135deg, #1a0a2e, #0f0f23);
    border: 1px solid rgba(123, 47, 255, 0.4);
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 20px 60px rgba(123, 47, 255, 0.2);
    max-width: 400px;
    margin: auto;
}
.stTextInput input {
    background: #1a0a2e !important;
    color: #f0e6ff !important;
    border: 1.5px solid rgba(180, 120, 255, 0.5) !important;
    border-radius: 10px !important;
}
.stTextInput input:focus {
    border-color: #7b2fff !important;
    box-shadow: 0 0 15px rgba(123, 47, 255, 0.3) !important;
}
.stButton button {
    background: linear-gradient(135deg, #7b2fff, #ff2fff) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    padding: 10px !important;
    box-shadow: 0 4px 15px rgba(123, 47, 255, 0.5) !important;
    transition: all 0.3s ease !important;
}
.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(123, 47, 255, 0.8) !important;
}
</style>
""", unsafe_allow_html=True)

# ===== GOOGLE SHEETS =====
SHEET_ID = "1KZ4bnjGkOAjCy_vto-ESkcyl7LessM4IQmfMlSICFC0"

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
        hashed = hash_password(password)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users_sheet.append_row([username, hashed, timestamp])
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

def save_chat(username, question, answer):
    chat_sheet, _ = get_sheets()
    if chat_sheet:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_sheet.append_row([timestamp, question, answer, username])

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
if "messages" not in st.session_state:
    st.session_state.messages = []
if "store" not in st.session_state:
    st.session_state.store = {}
if "page" not in st.session_state:
    st.session_state.page = "login"

# ===== HEADER =====
st.markdown("""
<div class="main-header">
    <h1>⚡ POWER AI</h1>
    <p>✦ Your Intelligent Assistant — Hindi & English ✦</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ===== LOGIN / REGISTER PAGE =====
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        with tab1:
            st.markdown("### Welcome Back!")
            username = st.text_input("Username:", key="login_user")
            password = st.text_input("Password:", type="password", key="login_pass")
            if st.button("Login ⚡", use_container_width=True):
                if username and password:
                    if login_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        # Load chat history
                        history = get_user_history(username)
                        st.session_state.messages = [
                            {"role": "user" if i % 2 == 0 else "assistant", "content": row["User Question"] if i % 2 == 0 else row["Bot Answer"]}
                            for i, row in enumerate(history)
                            for _ in range(2)
                        ]
                        st.rerun()
                    else:
                        st.error("❌ Wrong username or password!")
                else:
                    st.warning("⚠️ Sab fields bharo!")

        with tab2:
            st.markdown("### Create Account!")
            new_user = st.text_input("Username:", key="reg_user")
            new_pass = st.text_input("Password:", type="password", key="reg_pass")
            confirm_pass = st.text_input("Confirm Password:", type="password", key="reg_confirm")
            if st.button("Register ⚡", use_container_width=True):
                if new_user and new_pass and confirm_pass:
                    if new_pass != confirm_pass:
                        st.error("❌ Passwords match nahi kar rahe!")
                    else:
                        success, msg = register_user(new_user, new_pass)
                        if success:
                            st.success(f"✅ {msg} Ab login karo!")
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.warning("⚠️ Sab fields bharo!")

# ===== CHAT PAGE =====
else:
    # Top bar
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"👤 **{st.session_state.username}** ke saath baat kar raha hoon!")
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.messages = []
            st.session_state.store = {}
            st.rerun()

    # AI Setup
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Tum Power AI ho — ek powerful aur helpful AI assistant. User ka naam {st.session_state.username} hai. Hindi aur English dono mein baat kar sakte ho."),
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

    # Chat history load karo
    history = get_user_history(st.session_state.username)
    if history and not st.session_state.messages:
        for row in history:
            st.session_state.messages.append({"role": "user", "content": row["User Question"]})
            st.session_state.messages.append({"role": "assistant", "content": row["Bot Answer"]})

    # Messages dikhao
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input
    user_input = st.chat_input("⚡ Ask Anything To Power AI...")

    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("⚡ Power AI soch raha hai..."):
            response = chatbot.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": st.session_state.username}}
            )

        bot_reply = response.content
        with st.chat_message("assistant"):
            st.write(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        save_chat(st.session_state.username, user_input, bot_reply)