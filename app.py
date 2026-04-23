import streamlit as st
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import hashlib
from langchain_tavily import TavilySearch

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
search = TavilySearch(max_results=3)

from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

SHEET_ID = "1KZ4bnjGkOAjCy_vto-ESkcyl7LessM4IQmfMlSICFC0"

st.set_page_config(page_title="Power AI", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

:root {
    --bg: #0b0f14;
    --panel: #111823;
    --soft: rgba(255,255,255,0.04);
    --border: rgba(255,255,255,0.08);

    --text: #e8eef5;
    --muted: #93a4b5;

    --accent: #4f7cff;

    --radius: 14px;
}

/* ===== GLOBAL ===== */
.stApp {
    background: var(--bg);
    font-family: 'Inter', sans-serif;
    color: var(--text);
}

/* ===== HEADER (SAFE - DOES NOT BREAK TOGGLE) ===== */
header[data-testid="stHeader"] {
    background: transparent !important;
    border: none !important;
}

/* hide only decoration */
div[data-testid="stDecoration"] {
    display: none !important;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: var(--panel);
    border-right: 1px solid var(--border);
}

/* sidebar text */
[data-testid="stSidebar"] * {
    color: var(--text);
}

/* ===== CHAT LIST ===== */
.chat-item {
    padding: 10px 12px;
    border-radius: var(--radius);
    border: 1px solid transparent;
    color: var(--muted);
    transition: 0.2s ease;
    cursor: pointer;
}

.chat-item:hover {
    background: var(--soft);
    border-color: var(--border);
    color: var(--text);
}

.chat-item-active {
    background: rgba(79,124,255,0.12);
    border-color: rgba(79,124,255,0.35);
    color: var(--text);
}

/* ===== TITLE ===== */
.main-header {
    text-align: center;
    padding: 20px 10px;
}

.main-header h1 {
    font-size: 2rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.5px;
}

.main-header p {
    color: var(--muted);
    font-size: 0.85rem;
}

/* ===== INPUTS ===== */
.stTextInput input,
.stChatInput textarea {
    background: var(--panel);

    border-radius: var(--radius);
    color: var(--text);
    padding: 10px 12px;
}

.stTextInput input:focus,
.stChatInput textarea:focus {
    border-color: var(--accent);
    box-shadow: none !important;
    outline: none !important;
}

/* placeholder */
::placeholder {
    color: rgba(147,164,181,0.7) !important;
}

/* ===== CHAT BUBBLES ===== */
.stChatMessage {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px;
    margin: 8px 0;
}

.stChatMessage[data-testid="stChatMessageUser"] {
    background: rgba(255,255,255,0.03);
}

.stChatMessage[data-testid="stChatMessageAssistant"] {
    background: var(--panel);
}

/* text */
.stChatMessage p {
    color: var(--text);
    line-height: 1.6;
    font-size: 0.95rem;
}

/* ===== BUTTONS ===== */
.stButton button {
    background: var(--accent);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 500;
    transition: 0.2s ease;
}

.stButton button:hover {
    opacity: 0.9;
}

/* ===== CHAT INPUT BUTTON ===== */
.stChatInput button {
    background: var(--accent) !important;
    border-radius: 10px;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab"] {
    color: var(--muted);
}

.stTabs [aria-selected="true"] {
    color: var(--text);
    border-bottom: none !important;

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-thumb {
    background: rgba(255,255,255,0.15);
    border-radius: 10px;
}

/* ===== MOBILE RESPONSIVE ===== */
@media (max-width: 768px) {
    .main-header h1 {
        font-size: 1.5rem;
    }

    .stChatMessage {
        padding: 10px;
    }

    .stTextInput input,
    .stChatInput textarea {
        font-size: 0.95rem;
    }
}

/* ===== CLEANUP ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
            .stChatMessage {
    border: none !important;
    padding: 0 !important;
    margin: 8px 0 !important;
    background: transparent !important;
}

/* USER MESSAGE (RIGHT SIDE) */
.stChatMessage[data-testid="stChatMessageUser"] {
    display: flex;
    justify-content: flex-end;
}

.stChatMessage[data-testid="stChatMessageUser"] > div {
    background: #1f2a37;
    color: #ffffff;
    padding: 10px 14px;
    border-radius: 18px 18px 4px 18px;
    max-width: 80%;
    font-size: 0.95rem;
}

/* ASSISTANT MESSAGE (LEFT SIDE) */
.stChatMessage[data-testid="stChatMessageAssistant"] {
    display: flex;
    justify-content: flex-start;
}

.stChatMessage[data-testid="stChatMessageAssistant"] > div {
    background: #111823;
    color: #e8eef5;
    padding: 10px 14px;
    border-radius: 18px 18px 18px 4px;
    max-width: 80%;
    font-size: 0.95rem;
    border: 1px solid rgba(255,255,255,0.06);
}

/* MOBILE OPTIMIZATION */
@media (max-width: 768px) {
    .stChatMessage[data-testid="stChatMessageUser"] > div,
    .stChatMessage[data-testid="stChatMessageAssistant"] > div {
        max-width: 92%;
        font-size: 0.9rem;
    }
}
            [data-testid="stSidebar"] {
    background: #0f141b !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* sidebar items */
.chat-item {
    padding: 10px 12px;
    border-radius: 10px;
    transition: 0.2s ease;
    color: #94a3b8;
    font-size: 0.9rem;
}

.chat-item:hover {
    background: rgba(255,255,255,0.04);
    color: #ffffff;
}

/* active chat */
.chat-item-active {
    background: rgba(79,124,255,0.12);
    color: #ffffff;
    border-left: 2px solid #4f7cff;
}

/* sidebar title */
.sidebar-header h2 {
    font-size: 1rem;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 0.5px;
}            
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
            st.success("✅ Account Created! Login now!")

        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "👤 Guest"])

        with tab1:
            st.markdown("### Welcome Back!")
            username = st.text_input("Username:", key="login_user", placeholder="Enter your username")
            password = st.text_input("Password:", type="password", key="login_pass", placeholder="Enter your password")
            if st.button("Login ⚡", use_container_width=True, key="login_btn"):
                if username and password:
                    if login_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.is_guest = False
                        st.session_state.reg_success = False
                        st.session_state.messages = []
                        st.session_state.all_chats = {}

                        # load history
                        history = get_user_history(username)
                        for row in history:
                            cid = row.get("Chat ID", "default")
                            if cid not in st.session_state.all_chats:
                                st.session_state.all_chats[cid] = []
                            st.session_state.all_chats[cid].append({"role": "user", "content": row["User Question"]})
                            st.session_state.all_chats[cid].append({"role": "assistant", "content": row["Bot Answer"]})

                        # New Chat
                        new_id = datetime.now().strftime("%Y%m%d%H%M%S")
                        st.session_state.current_chat_id = new_id
                        st.session_state.messages = []
                        st.rerun()
                    else:
                        st.error("❌ Wrong username or password!")
                else:
                    st.warning("⚠️ Fill in all fields!")

        with tab2:
            st.markdown("### Create Account!")
            new_user = st.text_input("Username:", key="reg_user", placeholder="Enter your username")
            new_pass = st.text_input("Password:", type="password", key="reg_pass", placeholder="Enter a strong password")
            confirm_pass = st.text_input("Confirm Password:", type="password", key="reg_confirm", placeholder="Confirm your password")
            if st.button("Register ⚡", use_container_width=True, key="reg_btn"):
                if new_user and new_pass and confirm_pass:
                    if new_pass != confirm_pass:
                        st.error("❌ Passwords don't match!")
                    else:
                        success, msg = register_user(new_user, new_pass)
                        if success:
                            st.session_state.reg_success = True
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.warning("⚠️ Fill in all fields!")

        with tab3:
            st.markdown("### Guest Mode")
            st.info("You are in Guest Mode!")
            if st.button("Continue as Guest 👤", use_container_width=True, key="guest_btn"):
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

        # Show Old Chats
        if not st.session_state.is_guest and st.session_state.all_chats:
            st.markdown("**💬 Old Chats:**")
            for chat_id, chat_msgs in reversed(list(st.session_state.all_chats.items())):
                if chat_msgs:
                    # Show Question snippet as title
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

    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search"
        }
    ]
    llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2
)
    prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
    You are **Power AI** — an advanced, intelligent, and highly reliable AI assistant (2026 model), created by Dheeraj.

    ═══════════════════════════════════
    🧠 CORE IDENTITY
    ═══════════════════════════════════
    - You are sharp, accurate, and practical — not generic.
    - You think step-by-step internally but respond clearly and directly.
    - You give **high-value, structured, and actionable answers**.
    - You avoid fluff, repetition, and vague statements.

    ═══════════════════════════════════
    📅 CONTEXT
    ═══════════════════════════════════
    - Current Date: {datetime.now().strftime("%B %d, %Y")}
    - User Name: {st.session_state.username}

    ═══════════════════════════════════
    🌐 LANGUAGE INTELLIGENCE (STRICT RULE)
    ═══════════════════════════════════
    - ALWAYS match user's language style:
    • English → English  
    • Hindi → Hindi  
    • Hinglish → Hinglish (natural, not forced)
    - Never switch language unless user does.

    ═══════════════════════════════════
    🔎 WEB SEARCH DECISION SYSTEM
    ═══════════════════════════════════
    You MUST use web search when:
    - Query involves **latest updates (2026+)**
    - Topics like:
    • New tech (iPhone 17, AI tools, gadgets)
    • Current prices, specs, comparisons
    • News, trends, live data
    • Company updates or recent releases

    DO NOT search when:
    - Basic concepts (e.g., "What is Apex?")
    - Stable knowledge (math, theory, definitions)

    After searching:
    - Extract only **relevant, accurate insights**
    - Summarize in a **clean and structured format**
    - Avoid raw dumps or unnecessary details

    ═══════════════════════════════════
    ⚡ RESPONSE STYLE (VERY IMPORTANT)
    ═══════════════════════════════════
    - Start with a **clear answer**, then expand if needed
    - Use:
    • Bullet points for clarity
    • Headings for structure
    • Examples when helpful
    - Keep tone:
    → Smart
    → Helpful
    → Slightly conversational (not robotic)

    ═══════════════════════════════════
    🚀 INTELLIGENCE BOOST MODE
    ═══════════════════════════════════
    When user asks for:
    - Projects → Give real-world + step-by-step + pro tips
    - Comparisons → Give clear winner + reasoning
    - Learning → Break into simple + advanced path
    - Debugging → Identify issue + fix + explain why

    ═══════════════════════════════════
    ⚠️ STRICT DON'Ts
    ═══════════════════════════════════
    - Do NOT hallucinate facts
    - Do NOT guess outdated info → search instead
    - Do NOT give generic ChatGPT-style answers
    - Do NOT over-explain simple things

    ═══════════════════════════════════
    🎯 GOAL
    ═══════════════════════════════════
    Give answers that feel like:
    → Expert guidance
    → Not just information

    Always aim: **"User ko real value mile — not just response"**
    """),

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

    # Show Message
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input
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

        # Save
        if not st.session_state.is_guest:
            save_chat(st.session_state.username, user_input, bot_reply, st.session_state.current_chat_id)
            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()