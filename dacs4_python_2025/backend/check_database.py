"""Quick script to check database content"""
from modules.database import ChatDatabase
import colorama

colorama.init()

db = ChatDatabase()

print("\n" + "="*60)
print("DATABASE CONTENT CHECK")
print("="*60)

# Check users
print("\n[1] USERS:")
cursor = db.conn.cursor(dictionary=True)
cursor.execute("SELECT id, username, full_name FROM users")
users = cursor.fetchall()
for user in users:
    print(f"  - User #{user['id']}: {user['username']} ({user['full_name']})")

# Check conversations
print("\n[2] CONVERSATIONS:")
cursor.execute("SELECT id, user_id, title FROM conversations")
convs = cursor.fetchall()
for conv in convs:
    print(f"  - Conv #{conv['id']}: {conv['title']} (User #{conv['user_id']})")

# Check messages
print("\n[3] MESSAGES:")
cursor.execute("SELECT id, conversation_id, role, LEFT(content, 50) as content FROM messages")
msgs = cursor.fetchall()
for msg in msgs:
    print(f"  - Msg #{msg['id']}: [{msg['role']}] {msg['content']}... (Conv #{msg['conversation_id']})")

cursor.close()

print("\n" + "="*60)
print(f"Total: {len(users)} users, {len(convs)} conversations, {len(msgs)} messages")
print("="*60)
