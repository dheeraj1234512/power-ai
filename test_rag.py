#!/usr/bin/env python3
"""
Test script for the enhanced Power AI chatbot
"""

from chatbot import retriever, get_relevant_context

def test_rag():
    print("Testing RAG functionality...")

    # Test retriever setup
    if retriever:
        print("✅ Retriever initialized successfully")
    else:
        print("❌ Retriever failed to initialize")
        return

    # Test context retrieval
    test_queries = [
        "What services do you offer?",
        "How can I contact you?",
        "Tell me about Python"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        context = get_relevant_context(query)
        if context:
            print(f"Retrieved context: {context[:200]}...")
        else:
            print("No context retrieved")

    print("\n🎉 RAG test completed!")

if __name__ == "__main__":
    test_rag()