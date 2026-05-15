from langchain_groq import ChatGroq
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_tavily import TavilySearchResults
from dotenv import load_dotenv
import os
from datetime import datetime

# Load API Key from .env file
load_dotenv()

# Load API Key from .env file
load_dotenv()

# Groq AI Model
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2
)

# Web Search Tool
tavily_tool = TavilySearchResults(max_results=3)

# ===== RAG SETUP =====
def setup_rag():
    try:
        # Load knowledge base
        with open("knowledge_base.txt", "r", encoding="utf-8") as f:
            knowledge_text = f.read()

        # Split text into chunks
        text_splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=500,
            chunk_overlap=100
        )
        texts = text_splitter.split_text(knowledge_text)

        # Create embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # Create vector store
        vectorstore = FAISS.from_texts(texts, embeddings)

        # Create retriever
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        return retriever
    except Exception as e:
        print(f"RAG setup failed: {e}")
        return None

# Initialize RAG
retriever = setup_rag()

# Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are **Power AI** — a smart, reliable, and highly capable AI assistant.

Current Date: {current_date}

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

━━━━━━━━━━━━━━━━━━━━
📚 KNOWLEDGE BASE
━━━━━━━━━━━━━━━━━━━━
Use this information when relevant:
{context}
"""),

    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Make Chain with RAG
def get_relevant_context(query):
    context = ""
    if retriever:
        try:
            docs = retriever.invoke(query)
            context += "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"Retrieval failed: {e}")
    
    # Check if query needs current information
    current_keywords = ["current", "today", "now", "latest", "recent", "2024", "2025", "2026"]
    if any(keyword in query.lower() for keyword in current_keywords):
        try:
            search_results = tavily_tool.invoke({"query": query})
            search_context = "\n\n".join([result["content"] for result in search_results])
            context += f"\n\nRecent Web Search Results:\n{search_context}"
        except Exception as e:
            print(f"Search failed: {e}")
    
    return context

# Enhanced chain with context
from langchain_core.runnables import Runnable

class ContextAwareChain(Runnable):
    def invoke(self, inputs, config=None):
        query = inputs["input"]
        history = inputs.get("history", [])

        # Get relevant context
        context = get_relevant_context(query)

        # Get current date
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Format prompt with context
        formatted_prompt = prompt.format_messages(
            context=context,
            history=history,
            input=query,
            current_date=current_date
        )

        # Get response
        response = llm.invoke(formatted_prompt)
        return response

chain = ContextAwareChain()

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

# Start Chatbot (only when run directly)
if __name__ == "__main__":
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