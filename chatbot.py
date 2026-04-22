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
    ("system", """You are Power AI — a highly intelligent, reliable, and context-aware assistant designed to deliver accurate, practical, and insightful responses. User ka naam {username} hai. Communication Style:
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
username_input = input("Tumhara naam kya hai? (Enter for 'Guest'): ").strip()
if not username_input:
    username_input = "Guest"

while True:
    user_input = input("Tum: ")
    
    if user_input.lower() == "quit":
        print("Bot: Alvida! 👋")
        break
    
    response = chatbot.invoke(
        {"input": user_input, "username": username_input},
        config={"configurable": {"session_id": "user1"}}
    )
    print(f"Bot: {response.content}\n")