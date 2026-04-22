import streamlit as st
import os

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

/* ===== BACKGROUND ===== */
.stApp {
    background: radial-gradient(ellipse at top, #1a0a2e 0%, #0a0a0a 50%, #0d0015 100%);
    font-family: 'Rajdhani', sans-serif;
}

/* ===== ANIMATED GRID BACKGROUND ===== */
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

/* ===== HEADER ===== */
.main-header {
    text-align: center;
    padding: 30px 0 10px 0;
    position: relative;
}
.main-header h1 {
    font-family: 'Orbitron', sans-serif;
    font-size: 3.5em;
    font-weight: 900;
    background: linear-gradient(90deg, #7b2fff, #ff2fff, #00d4ff, #7b2fff);
    background-size: 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 4s ease infinite;
    text-shadow: none;
    letter-spacing: 5px;
    filter: drop-shadow(0 0 20px rgba(123, 47, 255, 0.8));
}
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.main-header p {
    color: #a78bfa !important;
    font-size: 1em;
    letter-spacing: 3px;
    text-transform: uppercase;
}

/* ===== USER CHAT BUBBLE ===== */
.stChatMessage[data-testid="stChatMessageUser"] {
    background: linear-gradient(135deg, #2d1b69 0%, #7b2fff 100%) !important;
    border-radius: 20px 20px 5px 20px !important;
    border: 1px solid rgba(123, 47, 255, 0.8) !important;
    box-shadow: 
        0 8px 32px rgba(123, 47, 255, 0.4),
        0 0 15px rgba(123, 47, 255, 0.2),
        inset 0 1px 0 rgba(255,255,255,0.1) !important;
    transform: perspective(1000px) rotateX(1deg);
    transition: all 0.3s ease !important;
    margin: 8px 0 !important;
}
.stChatMessage[data-testid="stChatMessageUser"]:hover {
    transform: perspective(1000px) rotateX(0deg) translateY(-2px);
    box-shadow: 
        0 15px 40px rgba(123, 47, 255, 0.6),
        0 0 25px rgba(123, 47, 255, 0.3) !important;
}

/* ===== BOT CHAT BUBBLE ===== */
.stChatMessage[data-testid="stChatMessageAssistant"] {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%) !important;
    border-radius: 20px 20px 20px 5px !important;
    border: 1px solid rgba(123, 47, 255, 0.4) !important;
    box-shadow: 
        0 8px 32px rgba(0, 0, 0, 0.5),
        0 0 15px rgba(123, 47, 255, 0.1),
        inset 0 1px 0 rgba(123, 47, 255, 0.1) !important;
    transform: perspective(1000px) rotateX(-1deg);
    transition: all 0.3s ease !important;
    margin: 8px 0 !important;
}
.stChatMessage[data-testid="stChatMessageAssistant"]:hover {
    transform: perspective(1000px) rotateX(0deg) translateY(-2px);
    box-shadow: 
        0 15px 40px rgba(0, 0, 0, 0.7),
        0 0 20px rgba(123, 47, 255, 0.2) !important;
}

/* ===== ALL TEXT WHITE ===== */
.stChatMessage p, .stChatMessage div, .stMarkdown p {
    color: #e2d9f3 !important;
    font-size: 1.05em !important;
    line-height: 1.6 !important;
}

/* ===== CHAT INPUT FIX ===== */
.stChatInput {
    position: relative;
}
.stChatInput textarea {
    background-color: #1a0a2e !important;
    color: #e2d9f3 !important;
    border: 2px solid rgba(123, 47, 255, 0.6) !important;
    border-radius: 15px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 1.1em !important;
    box-shadow: 
        0 0 20px rgba(123, 47, 255, 0.3),
        inset 0 2px 10px rgba(0,0,0,0.5) !important;
    transition: all 0.3s ease !important;
    caret-color: #7b2fff !important;
}
.stChatInput textarea:focus {
    border-color: #7b2fff !important;
    box-shadow: 
        0 0 30px rgba(123, 47, 255, 0.6),
        0 0 60px rgba(123, 47, 255, 0.2),
        inset 0 2px 10px rgba(0,0,0,0.5) !important;
    outline: none !important;
}
.stChatInput textarea::placeholder {
    color: #6b5a8a !important;
}

/* ===== SEND BUTTON ===== */
.stChatInput button {
    background: linear-gradient(135deg, #7b2fff, #ff2fff) !important;
    border: none !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 15px rgba(123, 47, 255, 0.5) !important;
    transition: all 0.3s ease !important;
}
.stChatInput button:hover {
    transform: scale(1.1) !important;
    box-shadow: 0 8px 25px rgba(123, 47, 255, 0.8) !important;
}
.stChatInput button svg {
    fill: white !important;
}

/* ===== SPINNER ===== */
.stSpinner > div {
    border-top-color: #7b2fff !important;
}

/* ===== DIVIDER ===== */
hr {
    border-color: rgba(123, 47, 255, 0.3) !important;
    box-shadow: 0 0 10px rgba(123, 47, 255, 0.2) !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { 
    background: linear-gradient(#7b2fff, #ff2fff);
    border-radius: 10px;
}

/* ===== HIDE STREAMLIT BRANDING ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown("""
<div class="main-header">
    <h1>⚡ POWER AI</h1>
    <p>✦ Your Intelligent Assistant — Hindi & English ✦</p>
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
    with st.chat_message("assistant"):
        st.write(response.content)
    st.session_state.messages.append({"role": "assistant", "content": response.content})