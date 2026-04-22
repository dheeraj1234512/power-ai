import streamlit as st
import os

# SABSE PEHLE API KEY SET KARO
if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

st.set_page_config(page_title="Power AI", page_icon="⚡", layout="centered")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 50%, #0a0a0a 100%);
    }
    .stChatInputContainer {
        background-color: #1a0a2e !important;
        border: 1px solid #7b2fff !important;
        border-radius: 15px !important;
    }
    .stChatInputContainer textarea { color: white !important; }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, #2d1b69, #7b2fff) !important;
        border-radius: 15px !important;
        color: white !important;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background-color: #1a1a2e !important;
        border: 1px solid #7b2fff !important;
        border-radius: 15px !important;
        color: white !important;
    }
    * { color: white !important; }
    .main-header { text-align: center; padding: 20px 0; }
    .main-header h1 {
        font-size: 3em;
        background: linear-gradient(90deg, #7b2fff, #ff2fff, #7b2fff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        letter-spacing: 3px;
    }
    .main-header p { color: #aaa !important; font-size: 1em; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>⚡ POWER AI</h1>
    <p>Your Intelligent Assistant — Hindi & English</p>
</div>
""", unsafe_allow_html=True)

st.divider()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Tum Power AI ho — ek powerful aur helpful AI assistant. Hindi aur English dono mein baat kar sakte ho."),
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

user_input = st.chat_input("⚡Ask Anything To Power AI ...")

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