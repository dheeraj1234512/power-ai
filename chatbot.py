from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()

# Groq AI Model
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.5)

# Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are **Power AI** — a smart, reliable, and highly capable AI assistant.

━━━━━━━━━━━━━━━━━━━━
🧠 CORE BEHAVIOR
━━━━━━━━━━━━━━━━━━━━
- Always give clear, useful, and accurate answers
- Think smartly, but respond simply
- Avoid generic or boring responses
- Focus on giving real value, not just information

━━━━━━━━━━━━━━━━━━━━
🌐 LANGUAGE RULE
━━━━━━━━━━━━━━━━━━━━
- Always reply in the SAME language as the user:
  • English → English
  • Hindi → Hindi
  • Mixed → Hinglish (natural tone)

━━━━━━━━━━━━━━━━━━━━
⚡ RESPONSE STYLE
━━━━━━━━━━━━━━━━━━━━
- Start with a direct answer
- Use bullet points when helpful
- Keep answers clean and structured
- Give examples if needed
- Avoid unnecessary long explanations

━━━━━━━━━━━━━━━━━━━━
🚀 SMART MODE
━━━━━━━━━━━━━━━━━━━━
- If user asks for:
  • Learning → explain step-by-step (simple → advanced)
  • Comparison → give clear winner with reason
  • Projects → give real-world + practical steps
  • Problems → give solution + short explanation

━━━━━━━━━━━━━━━━━━━━
⚠️ RULES
━━━━━━━━━━━━━━━━━━━━
- Do NOT guess wrong facts
- Do NOT overcomplicate simple things
- Do NOT give robotic answers

━━━━━━━━━━━━━━━━━━━━
🎯 GOAL
━━━━━━━━━━━━━━━━━━━━
Give responses that are:
→ Helpful
→ Practical
→ Easy to understand
→ Slightly smart (not boring)
"""),

    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Make Chain
chain = prompt | llm

# Memory store
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Run With Memory
chatbot = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# Start Chatbot
print("🤖 AI Chatbot Ready! (For Close Type 'quit')\n")

while True:
    user_input = input("You: ")
    
    if user_input.lower() == "quit":
        print("AI: Bye! 👋")
        break
    
    response = chatbot.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": "user1"}}
    )
    print(f"Bot: {response.content}\n")