# 📚 HƯỚNG DẪN CHAT HISTORY VỚI MYSQL

## 🎯 THAY ĐỔI CHÍNH

### 1. **Ẩn Webcam - Chạy Face Recognition Ẩn**
- ✅ Webcam không hiển thị trên giao diện
- ✅ Face recognition vẫn chạy background
- ✅ Video element được ẩn (`display: none`)

### 2. **Sidebar Lịch Sử Chat**
- ✅ Sidebar bên trái với danh sách conversations
- ✅ Button "New Chat" để tạo cuộc hội thoại mới
- ✅ Click vào conversation để load lịch sử
- ✅ Hiển thị user info và emotion

### 3. **MySQL Database**
- ✅ Lưu conversations và messages
- ✅ Theo dõi user sessions
- ✅ Tự động cập nhật timestamps

---

## 🗄️ CÀI ĐẶT DATABASE

### **Bước 1: Cài MySQL/MariaDB**

**Windows:**
```bash
# Download MySQL từ: https://dev.mysql.com/downloads/installer/
# Hoặc dùng XAMPP: https://www.apachefriends.org/
```

**Linux:**
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

### **Bước 2: Tạo Database**

```bash
# Login vào MySQL
mysql -u root -p

# Chạy schema
mysql -u root -p < backend/database/schema.sql
```

Hoặc copy nội dung `backend/database/schema.sql` và chạy trong MySQL Workbench.

### **Bước 3: Cấu hình .env**

Thêm vào `backend/.env`:
```env
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=voice_chat_db
```

### **Bước 4: Cài Python MySQL Connector**

```bash
cd backend
pip install mysql-connector-python
```

---

## 📊 DATABASE SCHEMA

### **Table: conversations**
```sql
- id: INT (Primary Key)
- user_name: VARCHAR(100)
- title: VARCHAR(255)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### **Table: messages**
```sql
- id: INT (Primary Key)
- conversation_id: INT (Foreign Key)
- role: ENUM('user', 'assistant')
- content: TEXT
- user_emotion: VARCHAR(50)
- created_at: TIMESTAMP
```

### **Table: user_sessions**
```sql
- id: INT (Primary Key)
- user_name: VARCHAR(100)
- conversation_id: INT
- started_at: TIMESTAMP
- ended_at: TIMESTAMP
```

---

## 🔧 SỬ DỤNG DATABASE MODULE

### **Test Database Connection:**

```bash
cd backend
python modules/database.py
```

### **Trong Code:**

```python
from modules.database import ChatDatabase

# Initialize
db = ChatDatabase()

# Create conversation
conv_id = db.create_conversation(user_name="John", title="New Chat")

# Add messages
db.add_message(conv_id, "user", "Hello!", user_emotion="happy")
db.add_message(conv_id, "assistant", "Hi there!")

# Get conversations
conversations = db.get_conversations(user_name="John", limit=50)

# Get messages
messages = db.get_messages(conv_id)

# Update title
db.update_conversation_title(conv_id, "Chat about AI")

# Delete conversation
db.delete_conversation(conv_id)

# Close connection
db.close()
```

---

## 🎨 FRONTEND MỚI

### **Files Mới:**
- `frontend/src/App_new.tsx` - Component mới với sidebar
- `frontend/src/index_new.css` - CSS mới cho layout sidebar

### **Thay Thế Files Cũ:**

```bash
cd frontend/src

# Backup files cũ
mv App.tsx App_old.tsx
mv index.css index_old.css

# Sử dụng files mới
mv App_new.tsx App.tsx
mv index_new.css index.css
```

### **Features:**
- ✅ Sidebar có thể đóng/mở
- ✅ Danh sách conversations
- ✅ Messages hiển thị như chat app
- ✅ Voice orb ở giữa màn hình
- ✅ User info ở sidebar footer

---

## 🔄 WEBSOCKET MESSAGES MỚI

### **Client → Server:**

```javascript
// Get conversations
{
  type: 'get_conversations',
  user_name: 'John' // or null
}

// Get messages
{
  type: 'get_messages',
  conversation_id: 123
}

// New conversation
{
  type: 'new_conversation',
  user_name: 'John' // or null
}
```

### **Server → Client:**

```javascript
// Conversations list
{
  type: 'conversations',
  conversations: [
    {
      id: 1,
      title: 'Chat about AI',
      updated_at: '2025-01-04T10:30:00'
    }
  ]
}

// Conversation created
{
  type: 'conversation_created',
  conversation_id: 123
}

// Messages
{
  type: 'messages',
  messages: [
    {
      role: 'user',
      content: 'Hello!',
      created_at: '2025-01-04T10:30:00'
    }
  ]
}
```

---

## 🚀 CHẠY HỆ THỐNG

### **1. Start MySQL:**
```bash
# Windows (XAMPP): Start MySQL từ Control Panel
# Linux:
sudo systemctl start mysql
```

### **2. Start Backend:**
```bash
cd backend
python server_rag.py
```

### **3. Start Frontend:**
```bash
cd frontend
npm run dev
```

### **4. Mở Browser:**
```
http://localhost:5173
```

---

## 🎯 WORKFLOW

### **Lần Đầu Sử Dụng:**
1. Click "CLICK TO START"
2. Cho phép quyền Camera + Mic
3. Face recognition chạy ẩn (không thấy video)
4. Nếu chưa đăng ký → Click "Register Face"
5. Hệ thống chào hỏi
6. Bắt đầu voice chat

### **Chat:**
1. Nói vào mic
2. VAD tự động phát hiện
3. STT → LLM → TTS
4. Messages tự động lưu vào database
5. Hiển thị trong sidebar

### **Xem Lịch Sử:**
1. Click vào conversation trong sidebar
2. Messages load từ database
3. Có thể tiếp tục chat trong conversation đó

### **Tạo Chat Mới:**
1. Click "New Chat"
2. Conversation mới được tạo
3. Messages cũ vẫn được lưu

---

## 🐛 TROUBLESHOOTING

### **Lỗi: Cannot connect to MySQL**
```bash
# Check MySQL đang chạy
sudo systemctl status mysql

# Check credentials trong .env
# Check port (default: 3306)
```

### **Lỗi: Table doesn't exist**
```bash
# Chạy lại schema
mysql -u root -p voice_chat_db < backend/database/schema.sql
```

### **Lỗi: Access denied for user**
```bash
# Tạo user mới hoặc cấp quyền
mysql -u root -p
CREATE USER 'voice_chat'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON voice_chat_db.* TO 'voice_chat'@'localhost';
FLUSH PRIVILEGES;
```

### **Webcam vẫn hiển thị**
- Đảm bảo đã thay `App.tsx` và `index.css` bằng files mới
- Clear browser cache
- Hard reload: `Ctrl + Shift + R`

---

## 📝 TODO (Tùy chọn)

### **Backend Integration:**
Cần cập nhật `server_rag.py` để:
1. Initialize database khi start
2. Tạo conversation khi user bắt đầu chat
3. Lưu messages vào database
4. Handle WebSocket messages mới (get_conversations, get_messages, etc.)

### **Auto Title Generation:**
Dùng LLM để tự động tạo title cho conversation:
```python
# Sau 2-3 messages đầu tiên
title = llm.chat("Summarize this conversation in 5 words: " + first_messages)
db.update_conversation_title(conv_id, title)
```

### **Search Feature:**
Thêm search box trong sidebar để tìm conversations.

### **Export Chat:**
Button để export conversation thành file text/PDF.

---

## 🎉 KẾT QUẢ

Sau khi hoàn thành, bạn sẽ có:
- ✅ Giao diện giống ChatGPT với sidebar
- ✅ Lịch sử chat được lưu vĩnh viễn
- ✅ Face recognition chạy ẩn
- ✅ Voice chat mượt mà
- ✅ User-friendly UI/UX

**Enjoy your new AI Voice Chat with History! 🚀**
