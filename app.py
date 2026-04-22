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
# NEW IMPORTS FOR HISTORY RESTORE
from langchain_core.messages import HumanMessage, AIMessage

SHEET_ID = "1KZ4bnjGkOAjCy_vto-ESkcyl7LessM4IQmfMlSICFC0"

st.set_page_config(page_title="Power AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ... (all your CSS stays exactly the same - I didn't touch it) ...
st.markdown("""<style> ... (your full CSS block) ...</style>""", unsafe_allow_html=True)

# ===== GOOGLE SHEETS =====
def get_sheets():
    return _get_sheets()

@st.cache_resource(ttl=3600)
def _get_sheets():
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

# FIXED: Correct column name + safety
def get_user_history(username):
    chat_sheet, _ = get_sheets()
    if chat_sheet:
        data = chat_sheet.get_all_records()
        return [row for row in data if row.get("Username") == username]
    return []

# NEW HELPER: Restore full conversation into LangChain memory when switching chats
def initialize_chat_history(chat_id: str, messages: list):
    if chat_id not in st.session_state.store:
        st.session_state.store[chat_id] = ChatMessageHistory()
    history = st.session_state.store[chat_id]
    history.clear()
    for msg in messages:
        if msg["role"] == "user":
            history.add_message(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history.add_message(AIMessage(content=msg["content"]))

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
if "logout_requested" not in st.session_state:
    st.session_state.logout_requested = False
if "login_requested" not in st.session_state:
    st.session_state.login_requested = False
if "login_username" not in st.session_state:
    st.session_state.login_username = ""

# Process pending cookie operations
if st.session_state.logout_requested:
    delete_login_cookie()
    st.session_state.logout_requested = False

if st.session_state.login_requested:
    set_login_cookie(st.session_state.login_username)
    st.session_state.login_requested = False
    st.session_state.login_username = ""

# Cookie login check
if not st.session_state.logged_in and not st.session_state.logout_requested:
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
    # (your entire login page code remains unchanged)
    st.markdown("""<div class="main-header">...</div>""", unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.reg_success:
            st.success("✅ Account Created! Please login now.")

        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "👤 Guest"])

        with tab1:
            # ... login tab unchanged ...
            pass
        with tab2:
            # ... register tab unchanged ...
            pass
        with tab3:
            # ... guest tab unchanged ...
            pass

# ===== CHAT PAGE =====
else:
    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown("""<div class="sidebar-header"><h2>⚡ POWER AI</h2></div>""", unsafe_allow_html=True)

        if st.button("➕ New Chat", use_container_width=True):
            new_id = datetime.now().strftime("%Y%m%d%H%M%S")
            if st.session_state.messages:
                st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()
            st.session_state.current_chat_id = new_id
            st.session_state.messages = []
            # REMOVED: st.session_state.store = {}  (no longer clearing memory)
            st.rerun()

        st.divider()

        if not st.session_state.is_guest and st.session_state.all_chats:
            st.markdown("**💬 History:**")
            for chat_id, chat_msgs in reversed(list(st.session_state.all_chats.items())):
                if chat_msgs:
                    first_q = chat_msgs[0]["content"][:30] + "..." if len(chat_msgs[0]["content"]) > 30 else chat_msgs[0]["content"]
                    is_active = chat_id == st.session_state.current_chat_id
                    css_class = "chat-item chat-item-active" if is_active else "chat-item"
                    st.markdown(f'<div class="{css_class}">💬 {first_q}</div>', unsafe_allow_html=True)
                    if st.button(f"Open", key=f"chat_{chat_id}"):
                        if st.session_state.messages:
                            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()
                        st.session_state.current_chat_id = chat_id
                        st.session_state.messages = chat_msgs.copy()
                        # CRITICAL FIX: Restore full history for LangChain
                        initialize_chat_history(chat_id, st.session_state.messages)
                        st.rerun()

        st.divider()

        if st.session_state.is_guest:
            st.markdown("👤 **Guest Mode**")
        else:
            st.markdown(f"👤 **{st.session_state.username}**")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logout_requested = True
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.is_guest = False
            st.session_state.messages = []
            st.session_state.store = {}
            st.session_state.all_chats = {}
            st.session_state.reg_success = False
            st.rerun()

    # ===== MAIN CHAT AREA =====
    st.markdown("""<div class="main-header"><h1>⚡ POWER AI</h1><p>✦ Your Intelligent Assistant ✦</p></div>""", unsafe_allow_html=True)
    st.divider()

    # AI Setup
    @st.cache_resource
    def get_llm():
        return ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
        
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are Power AI — a highly intelligent, reliable, and context-aware assistant designed to deliver accurate, practical, and insightful responses. User ka naam {st.session_state.username} hai. Communication Style:
        - Hindi aur English ka natural mix (Hinglish) use karo, based on user tone.
        - Clear, structured aur easy-to-understand responses do.
        - Overly robotic ya overly casual tone avoid karo — balanced, professional + friendly raho.
        Expert Mode:
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