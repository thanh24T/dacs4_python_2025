"""
Migration Script: Convert all users from Facenet (128D) to ArcFace (512D)
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import sys
import colorama
from modules.database import ChatDatabase
from modules.face_emotion import FaceEmotionDetector
import numpy as np
from deepface import DeepFace
import cv2
import base64

colorama.init()

def migrate_user_to_arcface(database, user_id, old_embedding):
    """
    Migrate a single user from Facenet to ArcFace
    Note: We can't convert embeddings directly, we need original images
    """
    print(colorama.Fore.YELLOW + f"[MIGRATE] User {user_id}: Cannot convert embedding without original image" + colorama.Style.RESET_ALL)
    print(colorama.Fore.YELLOW + f"[MIGRATE] User will need to re-register with face scan" + colorama.Style.RESET_ALL)
    return False

def main():
    print(colorama.Fore.CYAN + "=" * 60 + colorama.Style.RESET_ALL)
    print(colorama.Fore.CYAN + "  MIGRATION: Facenet (128D) → ArcFace (512D)" + colorama.Style.RESET_ALL)
    print(colorama.Fore.CYAN + "=" * 60 + colorama.Style.RESET_ALL)
    
    # Connect to database
    db = ChatDatabase()
    
    # Get all users
    users = db.get_all_users()
    
    if not users:
        print(colorama.Fore.YELLOW + "[MIGRATE] No users found in database" + colorama.Style.RESET_ALL)
        return
    
    print(colorama.Fore.CYAN + f"\n[MIGRATE] Found {len(users)} users" + colorama.Style.RESET_ALL)
    
    # Check embedding dimensions
    facenet_users = []
    arcface_users = []
    no_embedding_users = []
    
    for user in users:
        if not user.get('face_embedding'):
            no_embedding_users.append(user)
        else:
            embedding_dim = len(user['face_embedding'])
            if embedding_dim == 128:
                facenet_users.append(user)
            elif embedding_dim == 512:
                arcface_users.append(user)
            else:
                print(colorama.Fore.RED + f"[MIGRATE] User {user['user_id']}: Unknown embedding dimension {embedding_dim}" + colorama.Style.RESET_ALL)
    
    print(colorama.Fore.YELLOW + f"\n📊 Status:" + colorama.Style.RESET_ALL)
    print(f"  - Facenet (128D): {len(facenet_users)} users")
    print(f"  - ArcFace (512D): {len(arcface_users)} users")
    print(f"  - No embedding: {len(no_embedding_users)} users")
    
    if not facenet_users:
        print(colorama.Fore.GREEN + "\n✅ All users already using ArcFace!" + colorama.Style.RESET_ALL)
        return
    
    print(colorama.Fore.RED + f"\n⚠️  PROBLEM: {len(facenet_users)} users have old Facenet embeddings" + colorama.Style.RESET_ALL)
    print(colorama.Fore.YELLOW + "\n🔧 SOLUTIONS:" + colorama.Style.RESET_ALL)
    print("  1. Clear database and re-register all users (RECOMMENDED)")
    print("  2. Keep old users but they won't be recognized (need re-scan)")
    
    print(colorama.Fore.CYAN + "\n" + "=" * 60 + colorama.Style.RESET_ALL)
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        print(colorama.Fore.RED + "\n⚠️  This will DELETE all users and conversations!" + colorama.Style.RESET_ALL)
        confirm = input("Type 'YES' to confirm: ").strip()
        
        if confirm == "YES":
            cursor = db.connection.cursor()
            try:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                cursor.execute("DELETE FROM messages")
                cursor.execute("DELETE FROM user_sessions")
                cursor.execute("DELETE FROM conversations")
                cursor.execute("DELETE FROM users")
                cursor.execute("ALTER TABLE users AUTO_INCREMENT = 1")
                cursor.execute("ALTER TABLE conversations AUTO_INCREMENT = 1")
                cursor.execute("ALTER TABLE messages AUTO_INCREMENT = 1")
                cursor.execute("ALTER TABLE user_sessions AUTO_INCREMENT = 1")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                db.connection.commit()
                cursor.close()
                print(colorama.Fore.GREEN + "\n✅ Database cleared! Users can now register with ArcFace" + colorama.Style.RESET_ALL)
            except Exception as e:
                print(colorama.Fore.RED + f"❌ Error: {e}" + colorama.Style.RESET_ALL)
                db.connection.rollback()
                cursor.close()
        else:
            print(colorama.Fore.YELLOW + "❌ Cancelled" + colorama.Style.RESET_ALL)
    
    elif choice == "2":
        print(colorama.Fore.YELLOW + "\n⚠️  Old users will NOT be recognized" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "They need to scan face again to update to ArcFace" + colorama.Style.RESET_ALL)
        
        # Delete old embeddings so they can re-register
        for user in facenet_users:
            db.cursor.execute(
                "UPDATE users SET face_embedding = NULL WHERE user_id = %s",
                (user['user_id'],)
            )
        db.connection.commit()
        
        print(colorama.Fore.GREEN + f"\n✅ Cleared {len(facenet_users)} old embeddings" + colorama.Style.RESET_ALL)
        print(colorama.Fore.GREEN + "Users will be prompted to re-scan face on next login" + colorama.Style.RESET_ALL)
    
    else:
        print(colorama.Fore.YELLOW + "❌ Invalid choice" + colorama.Style.RESET_ALL)

if __name__ == "__main__":
    main()
