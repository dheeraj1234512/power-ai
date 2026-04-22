from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv

# API key load karo
load_dotenv()

# Groq AI Model (FREE!)
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

# Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", "Tum ek helpful AI assistant ho. Hindi aur English dono mein baat kar sakte ho."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Chain banao
chain = prompt | llm

# Memory store
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Memory ke saath chain
chatbot = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# Chatbot chalu karo!
print("🤖 AI Chatbot Ready! (band karne ke liye 'quit' likho)\n")

while True:
    user_input = input("Tum: ")
    
    if user_input.lower() == "quit":
        print("Bot: Alvida! 👋")
        break
    
    response = chatbot.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": "user1"}}
    )
    print(f"Bot: {response.content}\n")