"""
Automated Database Setup Script
Tự động tạo database và import schema
"""

import os
import sys
import colorama
import mysql.connector
from dotenv import load_dotenv

colorama.init()

# Load environment variables
load_dotenv()

print(colorama.Fore.CYAN + "=" * 70 + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "DATABASE SETUP - VOICE CHAT SYSTEM" + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "=" * 70 + colorama.Style.RESET_ALL)

# Get MySQL credentials
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'voice_chat_db')

if not MYSQL_PASSWORD:
    print(colorama.Fore.YELLOW + "\n⚠️  MySQL password not found in .env file!" + colorama.Style.RESET_ALL)
    MYSQL_PASSWORD = input("Enter MySQL root password: ")

print(f"\n📋 Configuration:")
print(f"   Host: {MYSQL_HOST}:{MYSQL_PORT}")
print(f"   User: {MYSQL_USER}")
print(f"   Database: {MYSQL_DATABASE}")

# Step 1: Connect to MySQL (without database)
print(colorama.Fore.CYAN + "\n[1/4] Connecting to MySQL..." + colorama.Style.RESET_ALL)
try:
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    cursor = conn.cursor()
    print(colorama.Fore.GREEN + "✅ Connected to MySQL!" + colorama.Style.RESET_ALL)
except Exception as e:
    print(colorama.Fore.RED + f"❌ Connection failed: {e}" + colorama.Style.RESET_ALL)
    print(colorama.Fore.YELLOW + "\nPlease check:" + colorama.Style.RESET_ALL)
    print("  1. MySQL is running")
    print("  2. Username and password are correct")
    print("  3. MySQL port is 3306")
    sys.exit(1)

# Step 2: Drop old database (if exists)
print(colorama.Fore.CYAN + f"\n[2/4] Dropping old database '{MYSQL_DATABASE}' (if exists)..." + colorama.Style.RESET_ALL)
try:
    cursor.execute(f"DROP DATABASE IF EXISTS {MYSQL_DATABASE}")
    print(colorama.Fore.GREEN + f"✅ Old database dropped!" + colorama.Style.RESET_ALL)
except Exception as e:
    print(colorama.Fore.YELLOW + f"⚠️  {e}" + colorama.Style.RESET_ALL)

# Step 3: Create new database
print(colorama.Fore.CYAN + f"\n[3/4] Creating new database '{MYSQL_DATABASE}'..." + colorama.Style.RESET_ALL)
try:
    cursor.execute(f"CREATE DATABASE {MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute(f"USE {MYSQL_DATABASE}")
    print(colorama.Fore.GREEN + f"✅ Database '{MYSQL_DATABASE}' created!" + colorama.Style.RESET_ALL)
except Exception as e:
    print(colorama.Fore.RED + f"❌ Failed to create database: {e}" + colorama.Style.RESET_ALL)
    sys.exit(1)

# Step 4: Import schema
print(colorama.Fore.CYAN + "\n[4/4] Importing schema from database/schema.sql..." + colorama.Style.RESET_ALL)
try:
    schema_file = "database/schema.sql"
    if not os.path.exists(schema_file):
        print(colorama.Fore.RED + f"❌ Schema file not found: {schema_file}" + colorama.Style.RESET_ALL)
        sys.exit(1)
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Split by semicolon and execute each statement
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    
    for statement in statements:
        # Skip USE database and CREATE DATABASE statements (already done)
        if statement.upper().startswith('USE ') or statement.upper().startswith('CREATE DATABASE'):
            continue
        
        try:
            cursor.execute(statement)
        except Exception as e:
            # Ignore "table already exists" errors
            if "already exists" not in str(e).lower():
                print(colorama.Fore.YELLOW + f"⚠️  {e}" + colorama.Style.RESET_ALL)
    
    conn.commit()
    print(colorama.Fore.GREEN + "✅ Schema imported successfully!" + colorama.Style.RESET_ALL)
    
except Exception as e:
    print(colorama.Fore.RED + f"❌ Failed to import schema: {e}" + colorama.Style.RESET_ALL)
    sys.exit(1)

# Verify tables
print(colorama.Fore.CYAN + "\n[VERIFY] Checking tables..." + colorama.Style.RESET_ALL)
cursor.execute("SHOW TABLES")
tables = [row[0] for row in cursor.fetchall()]

required_tables = ['users', 'conversations', 'messages', 'user_sessions']
missing_tables = [t for t in required_tables if t not in tables]

if missing_tables:
    print(colorama.Fore.RED + f"❌ Missing tables: {missing_tables}" + colorama.Style.RESET_ALL)
else:
    print(colorama.Fore.GREEN + f"✅ All tables created: {tables}" + colorama.Style.RESET_ALL)

# Close connection
cursor.close()
conn.close()

# Summary
print("\n" + colorama.Fore.GREEN + "=" * 70 + colorama.Style.RESET_ALL)
print(colorama.Fore.GREEN + "✅ DATABASE SETUP COMPLETE!" + colorama.Style.RESET_ALL)
print(colorama.Fore.GREEN + "=" * 70 + colorama.Style.RESET_ALL)

print(colorama.Fore.CYAN + "\n📊 Database Info:" + colorama.Style.RESET_ALL)
print(f"   Database: {MYSQL_DATABASE}")
print(f"   Tables: {len(tables)}")
print(f"   Status: Ready to use")

print(colorama.Fore.CYAN + "\n🚀 Next Steps:" + colorama.Style.RESET_ALL)
print("   1. Run test: python test_setup.py")
print("   2. Start server: python server_rag.py")
print("   3. Start frontend: cd ../frontend && npm run dev")
