"""Check if face embedding exists for users"""
from modules.database import ChatDatabase
import json

db = ChatDatabase()
cursor = db.conn.cursor(dictionary=True)

print("\n" + "="*70)
print("FACE EMBEDDING CHECK")
print("="*70)

cursor.execute("SELECT id, username, face_embedding FROM users")
users = cursor.fetchall()

for user in users:
    print(f"\nUser #{user['id']}: {user['username']}")
    
    if user['face_embedding']:
        try:
            embedding = json.loads(user['face_embedding'])
            print(f"  ✅ Face embedding: {len(embedding)} dimensions")
            print(f"  Sample values: {embedding[:5]}...")
        except:
            print(f"  ❌ Invalid JSON")
    else:
        print(f"  ❌ NO FACE EMBEDDING!")

cursor.close()
print("\n" + "="*70)
