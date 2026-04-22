import streamlit as st
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

# ===== GOOGLE SHEETS SETUP =====
SHEET_ID = "ESkcyl7LessM4IQmfMlSICFC0"  # Step 5 mein copy kiya tha

@st.cache_resource
def get_sheet():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://spreadsheets.google.com/feeds", 
                    "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except:
        return None

def save_to_sheet(question, answer, session_id):
    try:
        sheet = get_sheet()
        if sheet:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, question, answer, session_id])
            st.success("✅ Sheet mein save hua!")
        else:
            st.error("❌ Sheet connect nahi hui!")
    except Exception as e:
        st.error(f"❌ Error: {e}")

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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>⚡ POWER AI</h1>
    <p>✦ Your Intelligent Assistant ✦</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ===== AI SETUP =====
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Tum Power AI ho — ek powerful aur helpful AI assistant. Hindi aur English dono mein baat kar sakte ho. Hamesha polite aur helpful raho."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

chain = prompt | llm

if "store" not in st.session_state:
    st.session_state.store = {}
if "messages" not in st.session_state:
    st.session_state.messages = []

def get_session_history(session_id: str):
    if session_id not in st.session_state.store:
        st.session_state.store[session_id] = ChatMessageHistory()
    return st.session_state.store[session_id]

chatbot = RunnableWithMessageHistory(
    chain, get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# ===== CHAT =====
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("⚡ Ask Anything To Power AI...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("⚡ Power AI soch raha hai..."):
        response = chatbot.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": "user1"}}
        )

    bot_reply = response.content

    with st.chat_message("assistant"):
        st.write(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

    # Google Sheet mein save karo
    save_to_sheet(user_input, bot_reply, "user1")