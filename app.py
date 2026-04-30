import streamlit as st
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import hashlib
import secrets

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

# ===== CONSTANTS =====
SHEET_ID = "1KZ4bnjGkOAjCy_vto-ESkcyl7LessM4IQmfMlSICFC0"
TIMESTAMP_ID = "%Y%m%d%H%M%S"
TIMESTAMP_DATETIME = "%Y-%m-%d %H:%M:%S"
TIMESTAMP_DISPLAY = "%B %d, %Y"
MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2
GCP_SECRET_KEY = "gcp_service_account"
USERS_SHEET_NAME = "Users"

st.set_page_config(page_title="Power AI", page_icon="⚡", layout="wide")

# ===== SESSION STATE INITIALIZATION =====
def init_session_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "is_guest": False,
        "messages": [],
        "store": {},
        "current_chat_id": datetime.now().strftime(TIMESTAMP_ID),
        "all_chats": {},
        "active_tab": "login",
        "reg_success": False,
        "dark_mode": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ===== HELPER FUNCTIONS =====
def get_timestamp_id():
    return datetime.now().strftime(TIMESTAMP_ID)

def get_timestamp_datetime():
    return datetime.now().strftime(TIMESTAMP_DATETIME)

def get_timestamp_display():
    return datetime.now().strftime(TIMESTAMP_DISPLAY)

def handle_api_error(error: Exception) -> str:
    error_str = str(error).lower()
    if "rate_limit" in error_str or "429" in error_str:
        return "⚡ Server is busy! Please try again in a few minutes 🙏"
    return "Error processing request. Please try again."

def hash_password(password, salt=None):
    """Hash password with salt. If salt is None, generate a new one."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hashed}"

def verify_password(stored_hash, password):
    """Verify password against stored hash."""
    try:
        salt, hashed = stored_hash.split("$")
        return hash_password(password, salt) == stored_hash
    except ValueError:
        # Fallback for old unsalted hashes
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash

def reset_chat_state():
    """Reset chat messages and store."""
    st.session_state.messages = []
    st.session_state.store = {}

def reset_all_state():
    """Reset all chat state including history."""
    st.session_state.messages = []
    st.session_state.all_chats = {}
    st.session_state.store = {}

# ===== THEME & CSS =====
def get_theme_colors():
    if st.session_state.dark_mode:
        return {
            "bg": "#0b0f14",
            "panel": "#111823",
            "text": "#e8eef5",
            "muted": "#93a4b5",
            "soft": "rgba(255,255,255,0.04)",
            "border": "rgba(255,255,255,0.08)",
        }
    return {
        "bg": "#ffffff",
        "panel": "#f0f2f5",
        "text": "#1a1a1a",
        "muted": "#666666",
        "soft": "rgba(0,0,0,0.04)",
        "border": "rgba(0,0,0,0.1)",
    }

def get_css_styles(dark_mode=True):
    theme = get_theme_colors()
    bg = theme["bg"]
    panel = theme["panel"]
    text = theme["text"]
    muted = theme["muted"]
    soft = theme["soft"]
    border = theme["border"]

    # Chat bubble colors based on theme
    if dark_mode:
        user_msg_bg = "#1f2a37"
        user_msg_text = "#ffffff"
        assistant_msg_bg = "#111823"
        assistant_msg_text = "#e8eef5"
        placeholder_color = "rgba(147,164,181,0.7)"
    else:
        user_msg_bg = "#4f7cff"
        user_msg_text = "#ffffff"
        assistant_msg_bg = "#f0f2f5"
        assistant_msg_text = "#1a1a1a"
        placeholder_color = "rgba(100,100,100,0.5)"

    return f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

:root {{
    --bg: {bg};
    --panel: {panel};
    --soft: {soft};
    --border: {border};
    --text: {text};
    --muted: {muted};
    --accent: #4f7cff;
    --radius: 14px;
}}

.stApp {{
    background: var(--bg);
    font-family: 'Inter', sans-serif;
    color: var(--text);
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
    border: none !important;
}}

div[data-testid="stDecoration"] {{
    display: none !important;
}}

[data-testid="stSidebar"] {{
    background: var(--panel);
    border-right: 1px solid var(--border);
}}

[data-testid="stSidebar"] * {{
    color: var(--text);
}}

.chat-item {{
    padding: 10px 12px;
    border-radius: var(--radius);
    border: 1px solid transparent;
    color: var(--muted);
    transition: 0.2s ease;
    cursor: pointer;
}}

.chat-item:hover {{
    background: var(--soft);
    border-color: var(--border);
    color: var(--text);
}}

.chat-item-active {{
    background: rgba(79,124,255,0.12);
    border-color: rgba(79,124,255,0.35);
    color: var(--text);
}}

.main-header {{
    text-align: center;
    padding: 20px 10px;
}}

.main-header h1 {{
    font-size: 2rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: -0.5px;
}}

.main-header p {{
    color: var(--muted);
    font-size: 0.85rem;
}}

.stTextInput input, .stChatInput textarea {{
    background: var(--panel);
    border-radius: var(--radius);
    color: var(--text);
    padding: 10px 12px;
}}

.stTextInput input:focus, .stChatInput textarea:focus {{
    border-color: var(--accent);
    box-shadow: none !important;
    outline: none !important;
}}

::placeholder {{
    color: {placeholder_color} !important;
}}

.stChatMessage {{
    border: none !important;
    padding: 0 !important;
    margin: 8px 0 !important;
    background: transparent !important;
}}

.stChatMessage[data-testid="stChatMessageUser"] {{
    display: flex;
    justify-content: flex-end;
}}

.stChatMessage[data-testid="stChatMessageUser"] > div {{
    background: {user_msg_bg};
    color: {user_msg_text};
    padding: 10px 14px;
    border-radius: 18px 18px 4px 18px;
    max-width: 80%;
    font-size: 0.95rem;
}}

.stChatMessage[data-testid="stChatMessageUser"] * {{
    color: {user_msg_text} !important;
}}

.stChatMessage[data-testid="stChatMessageUser"] p {{
    color: {user_msg_text} !important;
}}

.stChatMessage[data-testid="stChatMessageAssistant"] {{
    display: flex;
    justify-content: flex-start;
}}

.stChatMessage[data-testid="stChatMessageAssistant"] > div {{
    background: {assistant_msg_bg};
    color: {assistant_msg_text};
    padding: 10px 14px;
    border-radius: 18px 18px 18px 4px;
    max-width: 80%;
    font-size: 0.95rem;
    border: 1px solid var(--border);
}}

.stChatMessage[data-testid="stChatMessageAssistant"] * {{
    color: {assistant_msg_text} !important;
}}

.stChatMessage[data-testid="stChatMessageAssistant"] p {{
    color: {assistant_msg_text} !important;
}}

.stButton button {{
    background: var(--accent);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 500;
    transition: 0.2s ease;
}}

.stButton button:hover {{
    opacity: 0.9;
}}

.stTabs [data-baseweb="tab"] {{
    color: var(--muted);
}}

.stTabs [aria-selected="true"] {{
    color: var(--text);
    border-bottom: none !important;
}}

::-webkit-scrollbar {{
    width: 6px;
}}

::-webkit-scrollbar-thumb {{
    background: rgba(255,255,255,0.15);
    border-radius: 10px;
}}

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

@media (max-width: 768px) {{
    .main-header h1 {{ font-size: 1.5rem; }}
    .stChatMessage {{ padding: 10px; }}
    .stChatMessage[data-testid="stChatMessageUser"] > div,
    .stChatMessage[data-testid="stChatMessageAssistant"] > div {{
        max-width: 92%;
        font-size: 0.9rem;
    }}
}}
"""

st.markdown(f"<style>{get_css_styles(st.session_state.dark_mode)}</style>", unsafe_allow_html=True)

# ===== GOOGLE SHEETS =====
@st.cache_resource
def get_sheets():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets[GCP_SECRET_KEY],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        workbook = client.open_by_key(SHEET_ID)
        return workbook.sheet1, workbook.worksheet(USERS_SHEET_NAME)
    except Exception as e:
        st.error(handle_api_error(e))
        return None, None

def register_user(username, password):
    _, users_sheet = get_sheets()
    if users_sheet:
        try:
            users = users_sheet.get_all_records()
            for user in users:
                if user.get("Username") == username:
                    return False, "Username already exists!"
            users_sheet.append_row([
                username,
                hash_password(password),
                get_timestamp_datetime()
            ])
            return True, "Registration successful!"
        except Exception as e:
            return False, handle_api_error(e)
    return False, "Database error!"

def login_user(username, password):
    _, users_sheet = get_sheets()
    if users_sheet:
        try:
            users = users_sheet.get_all_records()
            for user in users:
                if user.get("Username") == username and verify_password(user.get("Password", ""), password):
                    return True
        except Exception as e:
            st.error(handle_api_error(e))
    return False

def save_chat(username, question, answer, chat_id):
    chat_sheet, _ = get_sheets()
    if chat_sheet:
        try:
            chat_sheet.append_row([
                get_timestamp_datetime(),
                question,
                answer,
                username,
                chat_id
            ])
        except Exception as e:
            st.error(handle_api_error(e))

def get_user_history(username):
    chat_sheet, _ = get_sheets()
    if chat_sheet:
        try:
            data = chat_sheet.get_all_records()
            return [row for row in data if row.get("Username") == username]
        except Exception as e:
            st.error(handle_api_error(e))
    return []

def load_user_chat_history(username: str):
    """Load and structure user's chat history."""
    history = get_user_history(username)
    chats = {}
    for row in history:
        cid = row.get("Session ID") or row.get("Chat ID") or "default"
        if cid not in chats:
            chats[cid] = []
        chats[cid].append({"role": "user", "content": row.get("User Question", "")})
        chats[cid].append({"role": "assistant", "content": row.get("Bot Answer", "")})
    return chats

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
                        reset_all_state()
                        st.session_state.all_chats = load_user_chat_history(username)
                        st.session_state.current_chat_id = get_timestamp_id()
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
                reset_all_state()
                st.session_state.current_chat_id = get_timestamp_id()
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
            if st.session_state.messages:
                st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()
            st.session_state.current_chat_id = get_timestamp_id()
            reset_chat_state()
            st.rerun()

        st.divider()

        # Show Old Chats
        if not st.session_state.is_guest and st.session_state.all_chats:
            st.markdown("**💬 Old Chats:**")
            for chat_id, chat_msgs in reversed(list(st.session_state.all_chats.items())):
                if chat_msgs:
                    first_q = chat_msgs[0]["content"][:28] + "..." if len(chat_msgs[0]["content"]) > 28 else chat_msgs[0]["content"]
                    is_active = chat_id == st.session_state.current_chat_id
                    css_class = "chat-item chat-item-active" if is_active else "chat-item"
                    
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(f'<div class="{css_class}">💬 {first_q}</div>', unsafe_allow_html=True)
                        if st.button("Open", key=f"open_{chat_id}"):
                            if st.session_state.messages:
                                st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()
                            st.session_state.current_chat_id = chat_id
                            st.session_state.messages = chat_msgs.copy()
                            st.session_state.store = {}
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"del_{chat_id}"):
                            del st.session_state.all_chats[chat_id]
                            if st.session_state.current_chat_id == chat_id:
                                st.session_state.current_chat_id = get_timestamp_id()
                                reset_chat_state()
                            st.rerun()

        st.divider()

        # User info and theme toggle
        if st.session_state.is_guest:
            st.markdown("👤 **Guest Mode**")
        else:
            st.markdown(f"👤 **{st.session_state.username}**")

        if st.session_state.dark_mode:
            if st.button("☀️ Light Mode", use_container_width=True):
                st.session_state.dark_mode = False
                st.rerun()
        else:
            if st.button("🌙 Dark Mode", use_container_width=True):
                st.session_state.dark_mode = True
                st.rerun()



        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.is_guest = False
            reset_all_state()
            st.session_state.reg_success = False
            st.rerun()
        # Settings
        with st.expander("⚙️ Settings"):
            st.markdown("**🔐 Change Password**")
            old_pass = st.text_input("Current Password:", type="password", key="old_pass")
            new_pass = st.text_input("New Password:", type="password", key="new_pass")
            confirm_new = st.text_input("Confirm New Password:", type="password", key="confirm_new")
            
            if st.button("Update Password", use_container_width=True, key="update_pass"):
                if old_pass and new_pass and confirm_new:
                    if new_pass != confirm_new:
                        st.error("❌ Passwords don't match!")
                    elif not login_user(st.session_state.username, old_pass):
                        st.error("❌ Current password is wrong!")
                    else:
                        _, users_sheet = get_sheets()
                        if users_sheet:
                            users = users_sheet.get_all_records()
                            for i, user in enumerate(users):
                                if user.get("Username") == st.session_state.username:
                                    users_sheet.update_cell(i + 2, 2, hash_password(new_pass))
                                    st.success("✅ Password updated!")
                                    break
                else:
                    st.warning("⚠️ Fill all fields!")
    # ===== MAIN CHAT AREA =====
    st.markdown("""
    <div class="main-header">
        <h1>⚡ POWER AI</h1>
        <p>✦ Your Intelligent Assistant ✦</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # AI Setup
    def init_chatbot():
        llm = ChatGroq(model=MODEL_NAME, temperature=TEMPERATURE)
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
    - Current Date: {get_timestamp_display()}
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
    ⚡ RESPONSE STYLE (VERY IMPORTANT)
    ═══════════════════════════════════
    - Start with a **clear answer**, then expand if needed
    - Use bullet points for clarity
    - Keep tone smart, helpful, slightly conversational

    ═══════════════════════════════════
    🎯 GOAL
    ═══════════════════════════════════
    Give answers that feel like expert guidance, not just information.
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

        return RunnableWithMessageHistory(
            chain, get_session_history,
            input_messages_key="input",
            history_messages_key="history"
        )

    chatbot = init_chatbot()

    # Show Messages - Theme aware colors
    if st.session_state.dark_mode:
        user_bg, user_text = "#4f7cff", "#ffffff"
        assistant_bg, assistant_text = "#2d2d2d", "#e8eef5"
        assistant_border = "#404040"
    else:
        user_bg, user_text = "#4f7cff", "#ffffff"
        assistant_bg, assistant_text = "#f0f2f5", "#1a1a1a"
        assistant_border = "#e0e0e0"

    for msg in st.session_state.messages:
        # Escape HTML special characters
        content = (msg['content']
                  .replace('&', '&amp;')
                  .replace('<', '&lt;')
                  .replace('>', '&gt;')
                  .replace('"', '&quot;')
                  .replace("'", '&#39;'))

        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin: 8px 0;">
                <div style="background: {user_bg}; color: {user_text}; padding: 10px 14px; border-radius: 18px 18px 4px 18px; max-width: 80%; word-wrap: break-word; font-family: Inter, sans-serif; font-size: 0.95rem;">
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin: 8px 0;">
                <div style="background: {assistant_bg}; color: {assistant_text}; padding: 10px 14px; border-radius: 18px 18px 18px 4px; max-width: 80%; word-wrap: break-word; border: 1px solid {assistant_border}; font-family: Inter, sans-serif; font-size: 0.95rem;">
                    {content}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Input
    # Image upload
    col_input, col_upload = st.columns([11, 1])
    with col_upload:
        with st.popover("📎"):
            uploaded_image = st.file_uploader("Image Upload", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")
    with col_input:
        user_input = st.chat_input("⚡ Ask Anything To Power AI...")

    if user_input or uploaded_image:
        # Image handle karo
        image_content = None
        if uploaded_image:
            import base64
            image_bytes = uploaded_image.read()
            image_b64 = base64.b64encode(image_bytes).decode()
            image_type = uploaded_image.type
            image_content = f"data:{image_type};base64,{image_b64}"
            # Image dikhao
            st.image(uploaded_image, width=200)

        text_input = user_input or "Is image ke baare mein batao"

        content_escaped = (text_input
            .replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;')
            .replace("'", '&#39;'))
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; margin:8px 0;">
            <div style="background:{user_bg}; color:{user_text}; padding:10px 14px; border-radius:18px 18px 4px 18px; max-width:80%; word-wrap:break-word; font-family:Inter,sans-serif; font-size:0.95rem;">
                {content_escaped}
            </div>
        </div>""", unsafe_allow_html=True)

        st.session_state.messages.append({"role": "user", "content": text_input})

        with st.spinner("⚡ Thinking..."):
            try:
                if image_content:
                    # Vision wala request
                    from groq import Groq
                    client = Groq()
                    vision_response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": text_input},
                                    {"type": "image_url", "image_url": {"url": image_content}}
                                ]
                            }
                        ]
                    )
                    bot_reply = vision_response.choices[0].message.content
                else:
                    response = chatbot.invoke(
                        {"input": text_input},
                        config={"configurable": {"session_id": st.session_state.current_chat_id}}
                    )
                    bot_reply = response.content
            except Exception as e:
                bot_reply = handle_api_error(e)

        reply_escaped = (bot_reply
            .replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;')
            .replace("'", '&#39;'))
        placeholder = st.empty()
        displayed = ""
        for char in reply_escaped:
            displayed += char
            placeholder.markdown(f"""
            <div style="display:flex; justify-content:flex-start; margin:8px 0;">
                <div style="background:{assistant_bg}; color:{assistant_text}; padding:10px 14px; border-radius:18px 18px 18px 4px; max-width:80%; word-wrap:break-word; border:1px solid {assistant_border}; font-family:Inter,sans-serif; font-size:0.95rem;">
                    {displayed}▌
                </div>
            </div>""", unsafe_allow_html=True)
        placeholder.markdown(f"""
        <div style="display:flex; justify-content:flex-start; margin:8px 0;">
            <div style="background:{assistant_bg}; color:{assistant_text}; padding:10px 14px; border-radius:18px 18px 18px 4px; max-width:80%; word-wrap:break-word; border:1px solid {assistant_border}; font-family:Inter,sans-serif; font-size:0.95rem;">
                {reply_escaped}
            </div>
        </div>""", unsafe_allow_html=True)

        st.session_state.messages.append({"role": "assistant", "content": bot_reply})

        if not st.session_state.is_guest:
            save_chat(st.session_state.username, text_input, bot_reply, st.session_state.current_chat_id)
            st.session_state.all_chats[st.session_state.current_chat_id] = st.session_state.messages.copy()