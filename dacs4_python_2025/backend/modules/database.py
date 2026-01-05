"""
Database module for chat history with user management
MySQL/MariaDB connection and operations
"""

import mysql.connector
from mysql.connector import Error
import colorama
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ChatDatabase:
    def __init__(self):
        """Initialize database connection"""
        print(colorama.Fore.CYAN + "[DB] Connecting to MySQL..." + colorama.Style.RESET_ALL)
        
        self.config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'voice_chat_db'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        
        self.connection = None
        self.conn = None  # Alias for compatibility
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.conn = self.connection  # Alias for compatibility
            if self.connection.is_connected():
                print(colorama.Fore.GREEN + "[DB] ✅ Connected to MySQL!" + colorama.Style.RESET_ALL)
        except Error as e:
            print(colorama.Fore.RED + f"[DB] ❌ Connection failed: {e}" + colorama.Style.RESET_ALL)
            print(colorama.Fore.YELLOW + "[DB] Chat history will not be saved." + colorama.Style.RESET_ALL)
    
    def ensure_connection(self):
        """Ensure connection is alive"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
        except Error:
            self.connect()
    
    # ==================== USER MANAGEMENT ====================
    
    def create_user(self, username: str, full_name: str, face_embedding: list, 
                   gender: str = 'other', birth_year: int = None, age: int = None, 
                   avatar_url: str = None) -> Optional[int]:
        """Create a new user with profile"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO users (username, full_name, gender, birth_year, age, avatar_url, face_embedding) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            embedding_json = json.dumps(face_embedding)
            cursor.execute(query, (username, full_name, gender, birth_year, age, avatar_url, embedding_json))
            self.connection.commit()
            user_id = cursor.lastrowid
            cursor.close()
            print(colorama.Fore.GREEN + f"[DB] Created user #{user_id}: {username}" + colorama.Style.RESET_ALL)
            return user_id
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error creating user: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            
            if user and user.get('face_embedding'):
                user['face_embedding'] = json.loads(user['face_embedding'])
            
            return user
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting user: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            cursor.close()
            
            if user and user.get('face_embedding'):
                user['face_embedding'] = json.loads(user['face_embedding'])
            
            return user
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting user: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (for face recognition matching)"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT id, username, full_name, gender, age, avatar_url, face_embedding FROM users"
            cursor.execute(query)
            users = cursor.fetchall()
            cursor.close()
            
            for user in users:
                if user.get('face_embedding'):
                    user['face_embedding'] = json.loads(user['face_embedding'])
            
            return users
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting users: {e}" + colorama.Style.RESET_ALL)
            return []
    
    def update_user_profile(self, user_id: int, full_name: str = None, gender: str = None,
                           birth_year: int = None, age: int = None, avatar_url: str = None) -> bool:
        """Update user profile"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            updates = []
            params = []
            
            if full_name is not None:
                updates.append("full_name = %s")
                params.append(full_name)
            if gender is not None:
                updates.append("gender = %s")
                params.append(gender)
            if birth_year is not None:
                updates.append("birth_year = %s")
                params.append(birth_year)
            if age is not None:
                updates.append("age = %s")
                params.append(age)
            if avatar_url is not None:
                updates.append("avatar_url = %s")
                params.append(avatar_url)
            
            if not updates:
                return False
            
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, params)
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error updating user: {e}" + colorama.Style.RESET_ALL)
            return False
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login time"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "UPDATE users SET last_login = NOW() WHERE id = %s"
            cursor.execute(query, (user_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error updating last login: {e}" + colorama.Style.RESET_ALL)
            return False
    
    # ==================== CONVERSATION MANAGEMENT ====================
    
    def create_conversation(self, user_id: int, title: str = "New Chat") -> Optional[int]:
        """Create a new conversation for user"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO conversations (user_id, title) VALUES (%s, %s)"
            cursor.execute(query, (user_id, title))
            self.connection.commit()
            conversation_id = cursor.lastrowid
            cursor.close()
            print(colorama.Fore.GREEN + f"[DB] Created conversation #{conversation_id}" + colorama.Style.RESET_ALL)
            return conversation_id
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error creating conversation: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def add_message(self, conversation_id: int, role: str, content: str, user_emotion: Optional[str] = None) -> bool:
        """Add a message to conversation"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO messages (conversation_id, role, content, user_emotion) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (conversation_id, role, content, user_emotion))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error adding message: {e}" + colorama.Style.RESET_ALL)
            return False
    
    def get_conversations(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get list of conversations for a user"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)  # ✅ FIX: self.connection.cursor
            query = """
                SELECT id, user_id, title, created_at, updated_at 
                FROM conversations 
                WHERE user_id = %s 
                ORDER BY updated_at DESC 
                LIMIT %s
            """
            cursor.execute(query, (user_id, limit))
            conversations = cursor.fetchall()
            cursor.close()
            return conversations
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting conversations: {e}" + colorama.Style.RESET_ALL)
            return []
    
    def get_messages(self, conversation_id: int) -> List[Dict]:
        """Get all messages in a conversation"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT id, role, content, user_emotion, created_at 
                FROM messages 
                WHERE conversation_id = %s 
                ORDER BY created_at ASC
            """
            cursor.execute(query, (conversation_id,))
            messages = cursor.fetchall()
            cursor.close()
            return messages
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting messages: {e}" + colorama.Style.RESET_ALL)
            return []
    
    def update_conversation_title(self, conversation_id: int, title: str) -> bool:
        """Update conversation title"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "UPDATE conversations SET title = %s WHERE id = %s"
            cursor.execute(query, (title, conversation_id))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error updating title: {e}" + colorama.Style.RESET_ALL)
            return False
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation (cascade delete messages)"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "DELETE FROM conversations WHERE id = %s"
            cursor.execute(query, (conversation_id,))
            self.connection.commit()
            cursor.close()
            print(colorama.Fore.YELLOW + f"[DB] Deleted conversation #{conversation_id}" + colorama.Style.RESET_ALL)
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error deleting conversation: {e}" + colorama.Style.RESET_ALL)
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print(colorama.Fore.YELLOW + "[DB] Connection closed" + colorama.Style.RESET_ALL)
    
    # ==================== REMINDER MANAGEMENT ====================
    
    def create_reminder(self, user_id: int, title: str, reminder_time: str, description: str = None) -> Optional[int]:
        """Create a new reminder"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO reminders (user_id, title, description, reminder_time) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, title, description, reminder_time))
            self.connection.commit()
            reminder_id = cursor.lastrowid
            cursor.close()
            print(colorama.Fore.GREEN + f"[DB] Created reminder #{reminder_id}" + colorama.Style.RESET_ALL)
            return reminder_id
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error creating reminder: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def get_reminders(self, user_id: int, include_completed: bool = False) -> List[Dict]:
        """Get reminders for a user"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            if include_completed:
                query = "SELECT * FROM reminders WHERE user_id = %s ORDER BY reminder_time ASC"
            else:
                query = "SELECT * FROM reminders WHERE user_id = %s AND is_completed = FALSE ORDER BY reminder_time ASC"
            cursor.execute(query, (user_id,))
            reminders = cursor.fetchall()
            cursor.close()
            return reminders
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting reminders: {e}" + colorama.Style.RESET_ALL)
            return []
    
    def get_pending_reminders(self) -> List[Dict]:
        """Get all pending reminders that need to be triggered"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT r.*, u.username, u.full_name 
                FROM reminders r
                JOIN users u ON r.user_id = u.id
                WHERE r.is_completed = FALSE 
                AND r.is_notified = FALSE 
                AND r.reminder_time <= NOW()
            """
            cursor.execute(query)
            reminders = cursor.fetchall()
            cursor.close()
            return reminders
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting pending reminders: {e}" + colorama.Style.RESET_ALL)
            return []
    
    def mark_reminder_notified(self, reminder_id: int) -> bool:
        """Mark reminder as notified"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "UPDATE reminders SET is_notified = TRUE WHERE id = %s"
            cursor.execute(query, (reminder_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error marking reminder: {e}" + colorama.Style.RESET_ALL)
            return False
    
    def complete_reminder(self, reminder_id: int) -> bool:
        """Mark reminder as completed"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "UPDATE reminders SET is_completed = TRUE WHERE id = %s"
            cursor.execute(query, (reminder_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error completing reminder: {e}" + colorama.Style.RESET_ALL)
            return False
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "DELETE FROM reminders WHERE id = %s"
            cursor.execute(query, (reminder_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error deleting reminder: {e}" + colorama.Style.RESET_ALL)
            return False


# Test
if __name__ == "__main__":
    colorama.init()
    
    print("="*80)
    print("DATABASE TEST")
    print("="*80)
    
    db = ChatDatabase()
    
    if db.connection and db.connection.is_connected():
        # Test create conversation
        conv_id = db.create_conversation(user_name="John", title="Test Chat")
        
        if conv_id:
            # Test add messages
            db.add_message(conv_id, "user", "Hello!", "happy")
            db.add_message(conv_id, "assistant", "Hi there! How can I help?", None)
            
            # Test get messages
            messages = db.get_messages(conv_id)
            print(f"\nMessages in conversation #{conv_id}:")
            for msg in messages:
                print(f"  [{msg['role']}] {msg['content']}")
            
            # Test get conversations
            convs = db.get_conversations()
            print(f"\nAll conversations ({len(convs)}):")
            for conv in convs[:5]:
                print(f"  #{conv['id']}: {conv['title']} - {conv['updated_at']}")
        
        db.close()
    else:
        print("Database connection failed. Check your MySQL settings.")

    
    # ==================== REMINDER MANAGEMENT ====================
    
    def create_reminder(self, user_id: int, title: str, reminder_time: str, description: str = None) -> Optional[int]:
        """Create a new reminder"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO reminders (user_id, title, description, reminder_time) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, title, description, reminder_time))
            self.connection.commit()
            reminder_id = cursor.lastrowid
            cursor.close()
            print(colorama.Fore.GREEN + f"[DB] Created reminder #{reminder_id}" + colorama.Style.RESET_ALL)
            return reminder_id
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error creating reminder: {e}" + colorama.Style.RESET_ALL)
            return None
    
    def get_reminders(self, user_id: int, include_completed: bool = False) -> List[Dict]:
        """Get reminders for a user"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            if include_completed:
                query = "SELECT * FROM reminders WHERE user_id = %s ORDER BY reminder_time ASC"
            else:
                query = "SELECT * FROM reminders WHERE user_id = %s AND is_completed = FALSE ORDER BY reminder_time ASC"
            cursor.execute(query, (user_id,))
            reminders = cursor.fetchall()
            cursor.close()
            return reminders
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting reminders: {e}" + colorama.Style.RESET_ALL)
            return []
    
    def get_pending_reminders(self) -> List[Dict]:
        """Get all pending reminders that need to be triggered"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT r.*, u.username, u.full_name 
                FROM reminders r
                JOIN users u ON r.user_id = u.id
                WHERE r.is_completed = FALSE 
                AND r.is_notified = FALSE 
                AND r.reminder_time <= NOW()
            """
            cursor.execute(query)
            reminders = cursor.fetchall()
            cursor.close()
            return reminders
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting pending reminders: {e}" + colorama.Style.RESET_ALL)
            return []
    
    def mark_reminder_notified(self, reminder_id: int) -> bool:
        """Mark reminder as notified"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "UPDATE reminders SET is_notified = TRUE WHERE id = %s"
            cursor.execute(query, (reminder_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error marking reminder: {e}" + colorama.Style.RESET_ALL)
            return False
    
    def complete_reminder(self, reminder_id: int) -> bool:
        """Mark reminder as completed"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "UPDATE reminders SET is_completed = TRUE WHERE id = %s"
            cursor.execute(query, (reminder_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error completing reminder: {e}" + colorama.Style.RESET_ALL)
            return False
    
    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "DELETE FROM reminders WHERE id = %s"
            cursor.execute(query, (reminder_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error deleting reminder: {e}" + colorama.Style.RESET_ALL)
            return False
            return False

    def get_missed_reminders(self, user_id: int) -> List[Dict]:
        """Get all missed reminders for a user (notified but not completed)"""
        self.ensure_connection()
        if not self.connection or not self.connection.is_connected():
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT * FROM reminders
                WHERE user_id = %s 
                AND is_completed = FALSE 
                AND is_notified = TRUE
                ORDER BY reminder_time DESC
            """
            cursor.execute(query, (user_id,))
            reminders = cursor.fetchall()
            cursor.close()
            return reminders
        except Error as e:
            print(colorama.Fore.RED + f"[DB] Error getting missed reminders: {e}" + colorama.Style.RESET_ALL)
            return []
