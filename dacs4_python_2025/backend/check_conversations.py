from modules.database import ChatDatabase

db = ChatDatabase()
convs = db.get_conversations(1)

print('Conversations for user 1:')
for c in convs:
    print(f'  #{c["id"]}: {c["title"]} - {c["updated_at"]}')
