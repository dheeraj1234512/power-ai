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
SHEET_ID = "1KZ4bnjGkOAjCy_vto-ESkcyl7LessM4IQmfMlSICFC0"


def get_sheet():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        st.error(f"❌ Sheet Error: {e}")
        return None

def save_to_sheet(question, answer, session_id):
    try:
        sheet = get_sheet()
        if sheet:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, question, answer, session_id])
    except Exception as e:
        pass

st.set_page_config(page_title="Power AI", page_icon="⚡", layout="centered")

st.markdown("""
<style>
body {
    margin: 0;
    overflow-x: hidden;
}

/* ===== 3D BACKGROUND ===== */
.stApp {
    background: radial-gradient(circle at center, #0a0015, #000000);
    perspective: 1200px;
}

/* Moving gradient glow */
.stApp::before {
    content: "";
    position: fixed;
    width: 200%;
    height: 200%;
    top: -50%;
    left: -50%;
    background: radial-gradient(circle, rgba(123,47,255,0.15), transparent 60%);
    animation: moveBg 10s infinite linear;
    z-index: 0;
}

@keyframes moveBg {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* ===== GLASS CARD ===== */
.stChatMessage {
    backdrop-filter: blur(15px);
    transform-style: preserve-3d;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

/* ===== REAL 3D HOVER ===== */
.stChatMessage:hover {
    transform: rotateX(8deg) rotateY(8deg) scale(1.03);
    box-shadow: 0 30px 60px rgba(123,47,255,0.5);
}

/* ===== HEADER GLOW ===== */
.main-header h1 {
    text-shadow: 
        0 0 10px #7b2fff,
        0 0 20px #ff2fff,
        0 0 40px #00d4ff;
}

/* ===== CURSOR LIGHT EFFECT ===== */
.cursor-light {
    position: fixed;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(123,47,255,0.3), transparent 70%);
    pointer-events: none;
    transform: translate(-50%, -50%);
    z-index: 999;
}
</style>

<script>
document.addEventListener("mousemove", function(e) {
    let light = document.querySelector(".cursor-light");
    if (!light) {
        light = document.createElement("div");
        light.className = "cursor-light";
        document.body.appendChild(light);
    }
    light.style.left = e.clientX + "px";
    light.style.top = e.clientY + "px";
});
</script>
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

