import logging
import os
import re
from datetime import datetime
from functools import lru_cache
from dotenv import load_dotenv
import serpapi
from duckduckgo_search import DDGS
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("powerai")

GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-3.5")
TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", 0.2))
LIVE_SEARCH_COUNT = int(os.getenv("LIVE_SEARCH_COUNT", 4))

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

try:
    grok_model = ChatGroq(model=GROQ_MODEL_NAME, temperature=TEMPERATURE)
    logger.info("Initialized Grok model: %s", GROQ_MODEL_NAME)
except Exception as e:
    logger.error("Failed to initialize Grok model: %s", e)
    grok_model = None

claude_model = None
if ANTHROPIC_API_KEY:
    try:
        claude_model = ChatAnthropic(
            api_key=ANTHROPIC_API_KEY,
            model=CLAUDE_MODEL_NAME,
            temperature=TEMPERATURE,
        )
        logger.info("Initialized Claude model: %s", CLAUDE_MODEL_NAME)
    except Exception as e:
        logger.warning("Failed to initialize Claude model: %s", e)
else:
    logger.info("Claude API key not found. Using Grok only for now.")


def setup_rag():
    try:
        with open("knowledge_base.txt", "r", encoding="utf-8") as f:
            knowledge_text = f.read()

        text_splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=500,
            chunk_overlap=100,
        )
        texts = text_splitter.split_text(knowledge_text)

        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_texts(texts, embeddings)
        return vectorstore.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        logger.warning("RAG setup failed: %s", e)
        return None

retriever = setup_rag()

LIVE_PATTERN = re.compile(
    r"\b(current|today|now|latest|recent|news|price|stock|weather|exchange rate|exchange rates|market|update|breaking|trend|trending)\b",
    re.I,
)
COMPLEX_PATTERN = re.compile(
    r"\b(summarize|rewrite|reword|edit|compare|evaluation|evaluate|choose|strategy|plan|pros and cons|optimize|debug|review|criticize|improve|analysis)\b",
    re.I,
)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are Power AI, an expert assistant combining reasoning, training data, and current information as needed.

Current Date: {current_date}
Route: {route}
Route Reason: {route_reason}

Always answer in the user's language.
If the question is time-sensitive, favor live sources and mention that you used up-to-date information.
If the question is complex, use Claude when available.
Do not hallucinate.

Sources:
{context}
""",
    ),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])


def classify_intent(query: str) -> dict:
    normalized = query.lower().strip()
    if LIVE_PATTERN.search(normalized):
        return {
            "route": "live",
            "reason": "Detected a time-sensitive or current-events query",
            "confidence": 0.96,
        }
    if COMPLEX_PATTERN.search(normalized):
        return {
            "route": "claude",
            "reason": "Detected a complex reasoning, summarization, or comparison request",
            "confidence": 0.90,
        }
    return {
        "route": "grok",
        "reason": "Detected a general knowledge or reasoning request",
        "confidence": 0.82,
    }


@lru_cache(maxsize=128)
def get_live_search_context(query: str) -> tuple[str, str]:
    if SERPAPI_API_KEY:
        try:
            response = serpapi.search(
                q=query,
                engine="google",
                api_key=SERPAPI_API_KEY,
                num=LIVE_SEARCH_COUNT,
                output="json",
            )
            hits = []
            for item in response.get("organic_results", [])[:LIVE_SEARCH_COUNT]:
                title = item.get("title", "").strip()
                snippet = item.get("snippet", "").strip()
                link = item.get("link", "").strip()
                hits.append(f"{title}\n{snippet}\n{link}")
            if hits:
                return "\n\n".join(hits), "SerpAPI"
        except Exception as e:
            logger.warning("SerpAPI search failed: %s", e)

    try:
        ddgs = DDGS()
        duck_results = ddgs.text(query, max_results=LIVE_SEARCH_COUNT)
        hits = []
        for item in duck_results or []:
            title = item.get("title", "").strip()
            body = item.get("body", "").strip()
            href = item.get("href", "").strip()
            hits.append(f"{title}\n{body}\n{href}")
        if hits:
            return "\n\n".join(hits), "DuckDuckGo"
    except Exception as e:
        logger.warning("DuckDuckGo search failed: %s", e)

    return "", "none"


@lru_cache(maxsize=256)
def get_rag_context(query: str) -> str:
    if not retriever:
        return ""
    try:
        docs = retriever.invoke(query)
        return "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.warning("RAG retrieval failed: %s", e)
        return ""


class AssistantRouter(Runnable):
    def invoke(self, inputs, config=None):
        query = inputs["input"]
        history = inputs.get("history", [])

        route_info = classify_intent(query)
        rag_context = get_rag_context(query)
        live_context, live_source = ("", "")
        if route_info["route"] == "live":
            live_context, live_source = get_live_search_context(query)

        sources = []
        if rag_context:
            sources.append(f"Knowledge Base Context:\n{rag_context}")
        if live_context:
            sources.append(f"Live Search ({live_source}):\n{live_context}")
        context = "\n\n".join(sources) if sources else "No supporting context available."

        formatted_prompt = prompt.format_messages(
            current_date=datetime.now().strftime("%Y-%m-%d"),
            route=route_info["route"],
            route_reason=route_info["reason"],
            context=context,
            history=history,
            input=query,
        )

        target_model = grok_model
        if route_info["route"] in {"claude", "live"} and claude_model:
            target_model = claude_model

        if target_model is None:
            raise RuntimeError("No model is available to serve the request.")

        logger.info(
            "Routing query to %s using %s (source=%s)",
            route_info["route"],
            target_model.__class__.__name__,
            live_source or "knowledge_base",
        )

        response = target_model.invoke(formatted_prompt)
        content = getattr(response, "content", str(response))

        return {
            "content": content,
            "route": route_info["route"],
            "confidence": route_info["confidence"],
            "live_source": live_source,
        }


store: dict[str, ChatMessageHistory] = {}


def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


assistant = RunnableWithMessageHistory(
    AssistantRouter(),
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


if __name__ == "__main__":
    print("🤖 Power AI agent ready.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        response = assistant.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": "default"}},
        )
        print(response["content"] if isinstance(response, dict) else response)
