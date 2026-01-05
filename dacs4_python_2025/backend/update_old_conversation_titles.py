"""
Update titles for old conversations that still have "New Chat"
"""

import colorama
import asyncio
from modules.database import ChatDatabase
from modules.llm_cloudflare import LLMCloudflareHandler

colorama.init()

print("=" * 80)
print("UPDATE OLD CONVERSATION TITLES")
print("=" * 80)

# Initialize
db = ChatDatabase()
llm = LLMCloudflareHandler()

# Get all users
users = db.get_all_users()

for user in users:
    print(f"\n{colorama.Fore.CYAN}User: {user['username']}{colorama.Style.RESET_ALL}")
    
    # Get conversations
    conversations = db.get_conversations(user['id'], limit=100)
    
    for conv in conversations:
        # Only update if title is still "New Chat"
        if conv['title'] == 'New Chat':
            # Get messages
            messages = db.get_messages(conv['id'])
            
            if len(messages) >= 3:
                print(f"\n  Conv #{conv['id']}: {len(messages)} messages")
                
                # Format messages for title generation
                message_list = [
                    {"role": msg['role'], "content": msg['content']}
                    for msg in messages[:4]
                ]
                
                # Generate title
                title = llm.generate_conversation_title(message_list)
                
                if title and title != "New Chat":
                    # Update database
                    db.update_conversation_title(conv['id'], title)
                    print(f"    ✅ Updated: {colorama.Fore.GREEN}{title}{colorama.Style.RESET_ALL}")
                else:
                    print(f"    ⚠️  Failed to generate title")
            else:
                print(f"  Conv #{conv['id']}: Only {len(messages)} messages - skipping")

print("\n" + "=" * 80)
print("✅ DONE!")
print("=" * 80)
