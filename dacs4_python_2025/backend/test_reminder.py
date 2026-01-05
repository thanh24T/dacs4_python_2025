"""
Test reminder creation directly
"""

import colorama
from modules.database import ChatDatabase
from datetime import datetime, timedelta

colorama.init()

print("=" * 80)
print("TEST REMINDER CREATION")
print("=" * 80)

db = ChatDatabase()

# Get first user
users = db.get_all_users()
if not users:
    print(colorama.Fore.RED + "No users found! Please register a user first." + colorama.Style.RESET_ALL)
    exit(1)

user = users[0]
print(f"\nUser: {user['username']} (ID: {user['id']})")

# Create a test reminder for 1 minute from now
reminder_time = datetime.now() + timedelta(minutes=1)
reminder_time_str = reminder_time.strftime('%Y-%m-%d %H:%M:%S')

print(f"\nCreating reminder for: {reminder_time_str}")

reminder_id = db.create_reminder(
    user_id=user['id'],
    title="Test Reminder",
    reminder_time=reminder_time_str,
    description="This is a test reminder"
)

if reminder_id:
    print(colorama.Fore.GREEN + f"\n✅ Reminder created with ID: {reminder_id}" + colorama.Style.RESET_ALL)
    
    # Get all reminders
    reminders = db.get_reminders(user['id'])
    print(f"\nAll reminders for {user['username']}:")
    for r in reminders:
        print(f"  - {r['title']} at {r['reminder_time']}")
else:
    print(colorama.Fore.RED + "\n❌ Failed to create reminder" + colorama.Style.RESET_ALL)

print("\n" + "=" * 80)
