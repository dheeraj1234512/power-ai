import os
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dotenv import load_dotenv

# Load API Keys from .env file
load_dotenv()

# 1. Search Tool Setup (Internet Access)
search_tool = TavilySearchResults(max_results=3)
tools = [search_tool]

# 2. Groq AI Model
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2
)

# 3. Agent Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are **Power AI** — a smart, reliable, and highly capable AI assistant.

━━━━━━━━━━━━━━━━━━━━
🧠 CORE BEHAVIOR
━━━━━━━━━━━━━━━━━━━━
- If the user asks about recent events, facts after 2023, or current data, you MUST use the search tool.
- Always give clear, useful, and accurate answers.
- Think smartly, but respond simply.

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
- Start with a direct answer.
- Use proper markdown (bold, bullet points, code blocks).
- Give examples if needed.
"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"), # Important for agent thinking
])

# 4. Create Agent & Executor
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5. Memory Store
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# 6. Run With Memory
chatbot = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# Start Chatbot
if __name__ == "__main__":
    print("🤖 Power AI (Internet Connected) Ready! (Type 'quit' to exit)\n")

    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "quit":
            print("AI: Bye! 👋")
            break
        
        try:
            response = chatbot.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": "user1"}}
            )
            # Agent returns result in 'output' key
            print(f"Bot: {response['output']}\n")
        except Exception as e:
            print(f"Error: {e}\n")