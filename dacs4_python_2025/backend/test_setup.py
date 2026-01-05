"""
Test script to verify User Management System setup
"""

import colorama
colorama.init()

print(colorama.Fore.CYAN + "=" * 60 + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "TESTING USER MANAGEMENT SYSTEM SETUP" + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "=" * 60 + colorama.Style.RESET_ALL)

# Test 1: Database Connection
print("\n[1/5] Testing Database Connection...")
try:
    from modules.database import ChatDatabase
    db = ChatDatabase()
    print(colorama.Fore.GREEN + "✅ Database connected!" + colorama.Style.RESET_ALL)
except Exception as e:
    print(colorama.Fore.RED + f"❌ Database failed: {e}" + colorama.Style.RESET_ALL)
    exit(1)

# Test 2: Face Detector with Database
print("\n[2/5] Testing Face Detector...")
try:
    from modules.face_emotion import FaceEmotionDetector
    face_detector = FaceEmotionDetector(database=db)
    print(colorama.Fore.GREEN + "✅ Face detector initialized!" + colorama.Style.RESET_ALL)
except Exception as e:
    print(colorama.Fore.RED + f"❌ Face detector failed: {e}" + colorama.Style.RESET_ALL)
    exit(1)

# Test 3: Upload Folder
print("\n[3/5] Testing Upload Folder...")
import os
upload_folder = "uploads/avatars"
if os.path.exists(upload_folder):
    print(colorama.Fore.GREEN + f"✅ Upload folder exists: {upload_folder}" + colorama.Style.RESET_ALL)
else:
    print(colorama.Fore.YELLOW + f"⚠️ Creating upload folder: {upload_folder}" + colorama.Style.RESET_ALL)
    os.makedirs(upload_folder, exist_ok=True)
    print(colorama.Fore.GREEN + "✅ Upload folder created!" + colorama.Style.RESET_ALL)

# Test 4: Database Tables
print("\n[4/5] Testing Database Tables...")
try:
    # Check if tables exist
    cursor = db.conn.cursor(dictionary=True)
    cursor.execute("SHOW TABLES")
    tables = [row[list(row.keys())[0]] for row in cursor.fetchall()]
    cursor.close()
    
    required_tables = ['users', 'conversations', 'messages', 'user_sessions']
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print(colorama.Fore.RED + f"❌ Missing tables: {missing_tables}" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "Run: mysql -u root -p voice_chat_db < database/schema.sql" + colorama.Style.RESET_ALL)
        exit(1)
    else:
        print(colorama.Fore.GREEN + f"✅ All tables exist: {required_tables}" + colorama.Style.RESET_ALL)
except Exception as e:
    print(colorama.Fore.RED + f"❌ Table check failed: {e}" + colorama.Style.RESET_ALL)
    exit(1)

# Test 5: Test User CRUD
print("\n[5/5] Testing User CRUD Operations...")
try:
    # Get all users
    cursor = db.conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    cursor.close()
    
    print(colorama.Fore.GREEN + f"✅ Users in database: {user_count}" + colorama.Style.RESET_ALL)
    
    if user_count > 0:
        # Show sample user
        cursor = db.conn.cursor(dictionary=True)
        cursor.execute("SELECT username, full_name, gender, age FROM users LIMIT 1")
        sample_user = cursor.fetchone()
        cursor.close()
        
        print(colorama.Fore.CYAN + f"   Sample user: {sample_user['username']} ({sample_user['full_name']})" + colorama.Style.RESET_ALL)
    
except Exception as e:
    print(colorama.Fore.RED + f"❌ User CRUD test failed: {e}" + colorama.Style.RESET_ALL)
    exit(1)

# Summary
print("\n" + colorama.Fore.GREEN + "=" * 60 + colorama.Style.RESET_ALL)
print(colorama.Fore.GREEN + "✅ ALL TESTS PASSED!" + colorama.Style.RESET_ALL)
print(colorama.Fore.GREEN + "=" * 60 + colorama.Style.RESET_ALL)
print("\n" + colorama.Fore.CYAN + "System is ready to run!" + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "Start server: python server_rag.py" + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "Start frontend: cd ../frontend && npm run dev" + colorama.Style.RESET_ALL)
