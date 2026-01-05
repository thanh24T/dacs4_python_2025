"""
Check pending reminders
"""

import colorama
from modules.database import ChatDatabase

colorama.init()

db = ChatDatabase()

print("=" * 80)
print("PENDING REMINDERS CHECK")
print("=" * 80)

reminders = db.get_pending_reminders()

print(f"\nFound {len(reminders)} pending reminder(s):\n")

for r in reminders:
    print(f"  ID: {r['id']}")
    print(f"  Title: {r['title']}")
    print(f"  User: {r['username']} (ID: {r['user_id']})")
    print(f"  Time: {r['reminder_time']}")
    print(f"  Notified: {r['is_notified']}")
    print(f"  Completed: {r['is_completed']}")
    print()

print("=" * 80)
