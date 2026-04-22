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

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0520 0%, #0a0a1a 100%) !important;
    border-right: 1px solid rgba(123, 47, 255, 0.3) !important;
}
[data-testid="stSidebar"] * { color: #e2d9f3 !important; }

.sidebar-header {
    text-align: center;
    padding: 10px 0 20px 0;
}
.sidebar-header h2 {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.4em;
    background: linear-gradient(90deg, #7b2fff, #ff2fff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 900;
    letter-spacing: 3px;
}

.chat-item {
    background: rgba(123, 47, 255, 0.1);
    border: 1px solid rgba(123, 47, 255, 0.2);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 5px 0;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 0.9em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.chat-item:hover {
    background: rgba(123, 47, 255, 0.25);
    border-color: rgba(123, 47, 255, 0.5);
}
.chat-item-active {
    background: rgba(123, 47, 255, 0.3) !important;
    border-color: rgba(123, 47, 255, 0.8) !important;
}

/* ===== MAIN HEADER ===== */
.main-header { text-align: center; padding: 20px 0 10px 0; }
.main-header h1 {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.8em;
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
.main-header p { color: #a78bfa !important; font-size: 0.9em; letter-spacing: 3px; text-transform: uppercase; }

/* ===== LUXURY TEXT INPUT ===== */
.stTextInput input {
    background: linear-gradient(145deg, #120826, #1a0d35) !important;
    color: #f0e6ff !important;
    border: 1px solid rgba(139, 92, 246, 0.35) !important;
    border-radius: 12px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.1em !important;
    font-weight: 500 !important;
    letter-spacing: 0.5px !important;
    padding: 12px 16px !important;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.4) !important;
    transition: all 0.35s ease !important;
    caret-color: #c084fc !important;
    outline: none !important;
}
.stTextInput input:focus {
    border: 1px solid rgba(192, 132, 252, 0.7) !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.12), 0 0 20px rgba(139, 92, 246, 0.25) !important;
    outline: none !important;
}
.stTextInput input::placeholder { color: rgba(167, 139, 250, 0.35) !important; font-style: italic !important; }
.stTextInput input:focus-visible { outline: none !important; }
.stTextInput label {
    color: #a78bfa !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 0.9em !important;
    font-weight: 600 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}

/* ===== CHAT MESSAGES ===== */
.stChatMessage[data-testid="stChatMessageUser"] {
    background: linear-gradient(135deg, #2d1b69 0%, #7b2fff 100%) !important;
    border-radius: 20px 20px 5px 20px !important;
    border: 1px solid rgba(123, 47, 255, 0.8) !important;
    box-shadow: 0 8px 32px rgba(123, 47, 255, 0.4) !important;
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
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
    transform: perspective(1000px) rotateX(-1deg);
    transition: all 0.3s ease !important;
    margin: 8px 0 !important;
}
.stChatMessage[data-testid="stChatMessageAssistant"]:hover {
    transform: perspective(1000px) rotateX(0deg) translateY(-2px);
}
.stChatMessage p, .stChatMessage div { color: #e2d9f3 !important; font-size: 1.05em !important; line-height: 1.6 !important; }

/* ===== CHAT INPUT ===== */
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
.stChatInput button:hover { transform: scale(1.1) !important; }
.stChatInput button svg { fill: white !important; }

/* ===== BUTTONS ===== */
.stButton button {
    background: linear-gradient(135deg, #7b2fff, #ff2fff) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    box-shadow: 0 4px 15px rgba(123, 47, 255, 0.5) !important;
    transition: all 0.3s ease !important;
}
.stButton button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 25px rgba(123, 47, 255, 0.8) !important; }

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(123, 47, 255, 0.3) !important;
    gap: 8px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #a78bfa !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.1em !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
}
.stTabs [aria-selected="true"] {
    color: #ffffff !important;
    background: rgba(123, 47, 255, 0.2) !important;
    border-bottom: 2px solid #7b2fff !important;
}

input, textarea, select, button { outline: none !important; -webkit-tap-highlight-color: transparent !important; }
input:focus, textarea:focus { outline: none !important; }
input:focus-visible, textarea:focus-visible { outline: none !important; }
*:focus { outline: none !important; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: linear-gradient(#7b2fff, #ff2fff); border-radius: 10px; }
/* ===== SIDEBAR TOGGLE ===== */
section[data-testid="stSidebarCollapsedControl"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 9999 !important;
}
section[data-testid="stSidebarCollapsedControl"] button {
    background: linear-gradient(135deg, #7b2fff, #ff2fff) !important;
    border-radius: 0 10px 10px 0 !important;
    box-shadow: 4px 0 20px rgba(123, 47, 255, 0.6) !important;
    border: none !important;
    width: 32px !important;
    height: 64px !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}
section[data-testid="stSidebarCollapsedControl"] button svg {
    fill: white !important;
}
section[data-testid="stSidebarCollapsedControl"] button:hover {
    box-shadow: 4px 0 30px rgba(123, 47, 255, 0.9) !important;
    transform: scale(1.05) !important;
}
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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
    return False, "Database error!"

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

# ===== COOKIE MANAGER =====
cookie_manager = stx.CookieManager()

def set_login_cookie(username):
    cookie_manager.set("power_ai_user", username, expires_at=datetime.now() + timedelta(days=7))

def get_login_cookie():
    return cookie_manager.get("power_ai_user")

def delete_login_cookie():
    cookie_manager.delete("power_ai_user")

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
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "login"
if "reg_success" not in st.session_state:
    st.session_state.reg_success = False

# Cookie se login check karo
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
        <p>✦ Your Intelligent Assistant ✦</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.reg_success:
            st.success("✅ Account Created! Please login now.")

        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "👤 Guest"])

        with tab1:
            st.markdown("### Welcome Back!")
            username = st.text_input("Username:", key="login_user", placeholder="Enter your username")
            password = st.text_input("Password:", type="password", key="login_pass", placeholder="Enter your password")
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

                        # Purani history load karo aur chats mein group karo
                        history = get_user_history(username)
                        for row in history:
                            cid = row.get("Chat ID", "default")
                            if cid not in st.session_state.all_chats:
                                st.session_state.all_chats[cid] = []
                            st.session_state.all_chats[cid].append({"role": "user", "content": row["User Question"]})
                            st.session_state.all_chats[cid].append({"role": "assistant", "content": row["Bot Answer"]})

                        # Naya chat shuru karo
                        new_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        st.session_state.current_chat_id = new_id
                        st.session_state.messages = []
                        st.rerun()
                    else:
                        st.error("❌ Wrong username or password!")
                else:
                    st.warning("⚠️ Please fill in all fields!")

        with tab2:
            st.markdown("### Create Account!")
            new_user = st.text_input("Username:", key="reg_user", placeholder="Enter your username")
            new_pass = st.text_input("Password:", type="password", key="reg_pass", placeholder="Enter a strong password")
            confirm_pass = st.text_input("Confirm Password:", type="password", key="reg_confirm", placeholder="Enter your password again")
            if st.button("Register ⚡", use_container_width=True, key="reg_btn"):
                if new_user and new_pass and confirm_pass:
                    if new_pass != confirm_pass:
                        st.error("❌ Passwords do not match!")
                    else:
                        success, msg = register_user(new_user, new_pass)
                        if success:
                            st.session_state.reg_success = True
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.warning("⚠️ Please fill in all fields!")

        with tab3:
            st.markdown("### Guest Mode")
            st.info("⚠️ History will not be saved in Guest Mode!")
            if st.button("Guest Login 👤", use_container_width=True, key="guest_btn"):
                st.session_state.logged_in = True
                st.session_state.username = "Guest"
                st.session_state.is_guest = True
                st.session_state.messages = []
                st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d%H%M%S")
                st.rerun()

# ===== CHAT PAGE =====
else:
    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-header">
            <h2>⚡ POWER AI</h2>
        </div>
        """, unsafe_allow_html=True)

        # New Chat button
        if st.button("➕ New Chat", use_container_width=True):
            new_id = datetime.now().strftime("%Y%m%d%H%M%S")
            if st.session_state.messages:
                st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()
            st.session_state.current_chat_id = new_id
            st.session_state.messages = []
            st.session_state.store = {}
            st.rerun()

        st.divider()

        # Purani chats dikhao
        if not st.session_state.is_guest and st.session_state.all_chats:
            st.markdown("**💬 History:**")
            for chat_id, chat_msgs in reversed(list(st.session_state.all_chats.items())):
                if chat_msgs:
                    # Pehla sawaal dikhao chat ka naam ki tarah
                    first_q = chat_msgs[0]["content"][:30] + "..." if len(chat_msgs[0]["content"]) > 30 else chat_msgs[0]["content"]
                    is_active = chat_id == st.session_state.current_chat_id
                    css_class = "chat-item chat-item-active" if is_active else "chat-item"
                    st.markdown(f'<div class="{css_class}">💬 {first_q}</div>', unsafe_allow_html=True)
                    if st.button(f"Open", key=f"chat_{chat_id}"):
                        if st.session_state.messages:
                            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()
                        st.session_state.current_chat_id = chat_id
                        st.session_state.messages = chat_msgs.copy()
                        st.session_state.store = {}
                        st.rerun()

        st.divider()

        # User info aur logout
        if st.session_state.is_guest:
            st.markdown("👤 **Guest Mode**")
        else:
            st.markdown(f"👤 **{st.session_state.username}**")

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

    # ===== MAIN CHAT AREA =====
    st.markdown("""
    <div class="main-header">
        <h1>⚡ POWER AI</h1>
        <p>✦ Your Intelligent Assistant ✦</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # AI Setup
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are Power AI — a highly intelligent, reliable, and context-aware assistant designed to deliver accurate, practical, and insightful responses. User ka naam {st.session_state.username} hai. Communication Style:
        - Hindi aur English ka natural mix (Hinglish) use karo, based on user tone.
        - Clear, structured aur easy-to-understand responses do.
        - Overly robotic ya overly casual tone avoid karo — balanced, professional + friendly raho.Expert Mode:
        - Jab relevant ho, expert-level reasoning use karo (jaise developer, consultant, ya domain expert).
        - Complex cheezon ko simple breakdown me explain karo.
        - Jaha possible ho, best practices, pros-cons, aur alternatives bhi batao.

        User Personalization:
        - User ko naam se address karo jab natural lage.
        - Conversation context ya history ka use karo for continuity.

        Constraints:
        - Kabhi bhi misleading ya incorrect info mat do.
        - Agar kisi cheez ka sure nahi ho, clearly batao instead of fabricating.

        Goal:
        - Har response itna valuable ho ki user ko lage ki unhe premium-level guidance mil rahi hai."""),
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
                config={"configurable": {"session_id": st.session_state.current_chat_id}}
            )

        bot_reply = response.content
        with st.chat_message("assistant"):
            st.write(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        # Save karo
        if not st.session_state.is_guest:
            save_chat(st.session_state.username, user_input, bot_reply, st.session_state.current_chat_id)
            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()