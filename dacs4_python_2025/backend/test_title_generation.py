"""
Test Auto Title Generation
"""

import colorama
from modules.llm_cloudflare import LLMCloudflareHandler
from modules.database import ChatDatabase

colorama.init()

print("=" * 80)
print("TEST AUTO TITLE GENERATION")
print("=" * 80)

# Initialize
llm = LLMCloudflareHandler()
db = ChatDatabase()

# Test conversations
test_conversations = [
    [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing great! How can I help you today?"},
        {"role": "user", "content": "I need help with Python programming"}
    ],
    [
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "I don't have real-time weather data, but I can help you find weather info!"},
        {"role": "user", "content": "How do I check weather in Python?"}
    ],
    [
        {"role": "user", "content": "I'm feeling stressed about work"},
        {"role": "assistant", "content": "I understand. Take a deep breath. What's bothering you?"},
        {"role": "user", "content": "Too many deadlines"}
    ]
]

print("\nGenerating titles for test conversations...\n")

for i, messages in enumerate(test_conversations, 1):
    print(f"\n{'-' * 80}")
    print(f"Conversation {i}:")
    for msg in messages:
        print(f"  [{msg['role'].upper()}] {msg['content']}")
    
    title = llm.generate_conversation_title(messages)
    print(f"\n  📝 Generated Title: {colorama.Fore.GREEN}{title}{colorama.Style.RESET_ALL}")
    print(f"{'-' * 80}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE!")
print("=" * 80)
