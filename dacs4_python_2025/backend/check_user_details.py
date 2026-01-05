"""
Check user details including gender field
"""

import colorama
from modules.database import ChatDatabase

colorama.init()

db = ChatDatabase()

print("=" * 80)
print("USER DETAILS CHECK")
print("=" * 80)

users = db.get_all_users()

for user in users:
    print(f"\nUser #{user['id']}: {user['username']}")
    print(f"  Full Name: {user.get('full_name', 'N/A')}")
    print(f"  Gender: {user.get('gender', 'N/A')}")
    print(f"  Age: {user.get('age', 'N/A')}")
    print(f"  Avatar: {user.get('avatar_url', 'N/A')}")
    print(f"  Has Face Embedding: {bool(user.get('face_embedding'))}")

print("\n" + "=" * 80)
