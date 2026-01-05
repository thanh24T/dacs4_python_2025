"""
Script to clear all data from database
⚠️ WARNING: This will delete ALL users, conversations, and messages!
"""

from modules.database import ChatDatabase
import colorama

colorama.init()

print(colorama.Fore.RED + "=" * 70 + colorama.Style.RESET_ALL)
print(colorama.Fore.RED + "⚠️  WARNING: DATABASE CLEAR OPERATION" + colorama.Style.RESET_ALL)
print(colorama.Fore.RED + "=" * 70 + colorama.Style.RESET_ALL)

print("\nThis will DELETE ALL:")
print("  - Users")
print("  - Conversations")
print("  - Messages")
print("  - User sessions")

confirm = input("\nAre you sure? Type 'YES' to confirm: ")

if confirm != 'YES':
    print(colorama.Fore.YELLOW + "\n❌ Operation cancelled." + colorama.Style.RESET_ALL)
    exit(0)

print(colorama.Fore.CYAN + "\n[1/5] Connecting to database..." + colorama.Style.RESET_ALL)
db = ChatDatabase()

if not db.connection or not db.connection.is_connected():
    print(colorama.Fore.RED + "❌ Failed to connect to database!" + colorama.Style.RESET_ALL)
    exit(1)

cursor = db.connection.cursor()

try:
    # Disable foreign key checks temporarily
    print(colorama.Fore.CYAN + "\n[2/5] Disabling foreign key checks..." + colorama.Style.RESET_ALL)
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    # Clear messages
    print(colorama.Fore.CYAN + "[3/5] Clearing messages..." + colorama.Style.RESET_ALL)
    cursor.execute("DELETE FROM messages")
    messages_deleted = cursor.rowcount
    print(colorama.Fore.GREEN + f"  ✅ Deleted {messages_deleted} messages" + colorama.Style.RESET_ALL)
    
    # Clear user_sessions
    print(colorama.Fore.CYAN + "[4/5] Clearing user sessions..." + colorama.Style.RESET_ALL)
    cursor.execute("DELETE FROM user_sessions")
    sessions_deleted = cursor.rowcount
    print(colorama.Fore.GREEN + f"  ✅ Deleted {sessions_deleted} sessions" + colorama.Style.RESET_ALL)
    
    # Clear conversations
    print(colorama.Fore.CYAN + "[5/5] Clearing conversations..." + colorama.Style.RESET_ALL)
    cursor.execute("DELETE FROM conversations")
    convs_deleted = cursor.rowcount
    print(colorama.Fore.GREEN + f"  ✅ Deleted {convs_deleted} conversations" + colorama.Style.RESET_ALL)
    
    # Clear users
    print(colorama.Fore.CYAN + "[6/6] Clearing users..." + colorama.Style.RESET_ALL)
    cursor.execute("DELETE FROM users")
    users_deleted = cursor.rowcount
    print(colorama.Fore.GREEN + f"  ✅ Deleted {users_deleted} users" + colorama.Style.RESET_ALL)
    
    # Reset auto_increment
    print(colorama.Fore.CYAN + "\n[RESET] Resetting auto_increment..." + colorama.Style.RESET_ALL)
    cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE conversations AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE messages AUTO_INCREMENT = 1")
    cursor.execute("ALTER TABLE user_sessions AUTO_INCREMENT = 1")
    print(colorama.Fore.GREEN + "  ✅ Auto_increment reset" + colorama.Style.RESET_ALL)
    
    # Re-enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    # Commit changes
    db.connection.commit()
    
    print("\n" + colorama.Fore.GREEN + "=" * 70 + colorama.Style.RESET_ALL)
    print(colorama.Fore.GREEN + "✅ DATABASE CLEARED SUCCESSFULLY!" + colorama.Style.RESET_ALL)
    print(colorama.Fore.GREEN + "=" * 70 + colorama.Style.RESET_ALL)
    
    print(f"\nDeleted:")
    print(f"  - {users_deleted} users")
    print(f"  - {convs_deleted} conversations")
    print(f"  - {messages_deleted} messages")
    print(f"  - {sessions_deleted} sessions")
    
    print(colorama.Fore.CYAN + "\n📝 Database is now empty and ready for fresh data!" + colorama.Style.RESET_ALL)
    
except Exception as e:
    print(colorama.Fore.RED + f"\n❌ Error: {e}" + colorama.Style.RESET_ALL)
    db.connection.rollback()
finally:
    cursor.close()
    db.connection.close()
