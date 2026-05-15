#!/usr/bin/env python3
"""
Training Script for Power AI Chatbot
This script helps analyze conversations and improve the chatbot's performance.
"""

import pandas as pd
from collections import Counter
import re
from datetime import datetime
import json

class ChatbotTrainer:
    def __init__(self):
        self.conversations = []
        self.feedback_data = []

    def load_conversation_data(self, file_path="conversations.csv"):
        """Load conversation data from CSV file"""
        try:
            df = pd.read_csv(file_path)
            self.conversations = df.to_dict('records')
            print(f"Loaded {len(self.conversations)} conversations")
        except FileNotFoundError:
            print("No conversation data found. Starting fresh.")
            self.conversations = []

    def analyze_conversations(self):
        """Analyze conversation patterns and generate insights"""
        if not self.conversations:
            return {
                "total_conversations": 0,
                "avg_response_length": 0,
                "common_topics": [],
                "user_satisfaction": 0,
                "improvement_areas": ["Collect more conversation data"]
            }

        analysis = {
            "total_conversations": len(self.conversations),
            "avg_response_length": 0,
            "common_topics": [],
            "user_satisfaction": 0,
            "improvement_areas": []
        }

        # Calculate average response length
        response_lengths = []
        topics = []

        for conv in self.conversations:
            if 'response' in conv:
                response_lengths.append(len(str(conv['response'])))
            if 'topic' in conv:
                topics.append(conv['topic'])

        if response_lengths:
            analysis["avg_response_length"] = sum(response_lengths) / len(response_lengths)

        # Find common topics
        if topics:
            topic_counts = Counter(topics)
            analysis["common_topics"] = topic_counts.most_common(5)

        return analysis

    def generate_training_suggestions(self, analysis):
        """Generate suggestions based on analysis"""
        suggestions = []

        if analysis["avg_response_length"] < 50:
            suggestions.append("Responses are too short. Consider adding more detailed explanations.")

        if analysis["total_conversations"] < 100:
            suggestions.append("Collect more conversation data for better training insights.")

        if not analysis["common_topics"]:
            suggestions.append("Add topic classification to conversations for better analysis.")

        return suggestions

    def update_knowledge_base(self, new_info, category="general"):
        """Add new information to knowledge base"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "timestamp": timestamp,
            "category": category,
            "content": new_info,
            "source": "training_script"
        }

        # Append to knowledge base file
        try:
            with open("knowledge_base.txt", "a", encoding="utf-8") as f:
                f.write(f"\n\n## {category.title()} - {timestamp}\n{new_info}")
            print(f"Added new information to knowledge base: {category}")
        except Exception as e:
            print(f"Error updating knowledge base: {e}")

    def export_training_data(self, filename="training_export.json"):
        """Export training data for external model training"""
        training_data = {
            "conversations": self.conversations,
            "analysis": self.analyze_conversations(),
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)

        print(f"Training data exported to {filename}")

def main():
    trainer = ChatbotTrainer()

    # Load existing data
    trainer.load_conversation_data()

    # Analyze conversations
    analysis = trainer.analyze_conversations()
    print("\n=== CONVERSATION ANALYSIS ===")
    for key, value in analysis.items():
        print(f"{key}: {value}")

    # Generate suggestions
    suggestions = trainer.generate_training_suggestions(analysis)
    print("\n=== TRAINING SUGGESTIONS ===")
    for suggestion in suggestions:
        print(f"- {suggestion}")

    # Example: Add new knowledge
    print("\n=== ADDING SAMPLE KNOWLEDGE ===")
    trainer.update_knowledge_base(
        "Power AI supports multiple languages including English, Hindi, and Hinglish.",
        "language_support"
    )

    # Export training data
    trainer.export_training_data()

if __name__ == "__main__":
    main()