#!/usr/bin/env python3
"""
Test script for the enhanced Power AI chatbot
"""

from chatbot import classify_intent, get_rag_context, get_live_search_context, assistant

def test_rag():
    print("Testing Power AI assistant routing and retrieval...")

    intent_samples = [
        "What are the latest AI news for 2026?",
        "Summarize the benefits of prompt engineering.",
        "What services do you offer?"
    ]

    for query in intent_samples:
        route = classify_intent(query)
        print(f"\nQuery: {query}")
        print(f"Routed to: {route['route']} (reason: {route['reason']})")

    context = get_rag_context("Tell me about Python programming.")
    print(f"\nRAG context length: {len(context)}")

    live_text, live_source = get_live_search_context("Latest AI released today")
    print(f"Live search source: {live_source}")
    print(f"Live text length: {len(live_text)}")

    print("\nAssistant loaded:", assistant is not None)
    print("\n🎉 RAG test completed!")

if __name__ == "__main__":
    test_rag()