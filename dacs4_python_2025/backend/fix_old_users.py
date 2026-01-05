"""
Fix old users without gender field
"""

import colorama
from modules.database import ChatDatabase

colorama.init()

db = ChatDatabase()

print("=" * 80)
print("FIX OLD USERS - ADD DEFAULT GENDER")
print("=" * 80)

# Get all users
users = db.get_all_users()

for user in users:
    if not user.get('gender'):
        print(f"\nFixing user #{user['id']}: {user['username']}")
        
        # Update with default gender
        success = db.update_user_profile(
            user_id=user['id'],
            gender='other'
        )
        
        if success:
            print(colorama.Fore.GREEN + f"  ✅ Updated gender to 'other'" + colorama.Style.RESET_ALL)
        else:
            print(colorama.Fore.RED + f"  ❌ Failed to update" + colorama.Style.RESET_ALL)
    else:
        print(f"\nUser #{user['id']}: {user['username']} - Already has gender: {user['gender']}")

print("\n" + "=" * 80)
print("✅ DONE!")
print("=" * 80)
