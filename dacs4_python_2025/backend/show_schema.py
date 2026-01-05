"""Show database schema"""
from modules.database import ChatDatabase

db = ChatDatabase()
cursor = db.conn.cursor(dictionary=True)

print("\n" + "="*60)
print("USERS TABLE SCHEMA")
print("="*60)

cursor.execute("DESCRIBE users")
cols = cursor.fetchall()

for col in cols:
    print(f"{col['Field']:20} {col['Type']:20} {col['Null']:5} {col['Key']:5}")

cursor.close()
