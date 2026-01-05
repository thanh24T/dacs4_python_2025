# 👤 HƯỚNG DẪN QUẢN LÝ USER VỚI FACE RECOGNITION

## 🎯 TÍNH NĂNG

### **1. Đăng Ký Tự Động**
- Khi mở app, tự động quét khuôn mặt
- Nếu là user mới → Hiển thị form đăng ký
- Nếu đã đăng ký → Tự động đăng nhập

### **2. Form Đăng Ký Đầy Đủ**
- **Avatar:** Upload ảnh đại diện
- **Tên đầy đủ:** Họ và tên
- **Username:** Tên đăng nhập (unique)
- **Giới tính:** Male / Female / Other
- **Năm sinh:** Birth year
- **Tuổi:** Tự động tính hoặc nhập

### **3. User Profile & Settings**
- Xem và chỉnh sửa thông tin cá nhân
- Thay đổi avatar
- Cập nhật thông tin

### **4. Chat History Riêng Biệt**
- Mỗi user có lịch sử chat riêng
- Không thấy chat của user khác
- Tự động load khi đăng nhập

---

## 🗄️ DATABASE SCHEMA MỚI

### **Table: users**
```sql
- id: INT (Primary Key)
- username: VARCHAR(100) UNIQUE
- full_name: VARCHAR(255)
- gender: ENUM('male', 'female', 'other')
- birth_year: INT
- age: INT
- avatar_url: VARCHAR(500)
- face_embedding: JSON (face recognition data)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- last_login: TIMESTAMP
```

### **Table: conversations** (Updated)
```sql
- id: INT (Primary Key)
- user_id: INT (Foreign Key → users.id)
- title: VARCHAR(255)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### **Table: messages** (Unchanged)
```sql
- id: INT (Primary Key)
- conversation_id: INT (Foreign Key)
- role: ENUM('user', 'assistant')
- content: TEXT
- user_emotion: VARCHAR(50)
- created_at: TIMESTAMP
```

---

## 🔄 WORKFLOW

### **Lần Đầu Mở App:**
```
1. User mở app
2. Click "CLICK TO START"
3. Cho phép quyền Camera + Mic
4. Face recognition quét khuôn mặt (ẩn)
5. Kiểm tra database:
   - Nếu CHƯA đăng ký → Hiển thị Registration Form
   - Nếu ĐÃ đăng ký → Auto login + Load chat history
```

### **Registration Form:**
```
┌─────────────────────────────────────┐
│     WELCOME! LET'S GET STARTED      │
├─────────────────────────────────────┤
│                                     │
│  [  Upload Avatar  ]                │
│                                     │
│  Full Name: [________________]      │
│  Username:  [________________]      │
│  Gender:    ( ) Male                │
│             ( ) Female              │
│             ( ) Other               │
│  Birth Year: [____]                 │
│  Age:       [__]                    │
│                                     │
│  [ Cancel ]      [ Register ]       │
└─────────────────────────────────────┘
```

### **Auto Login:**
```
1. Face detected
2. Match với database
3. Load user profile
4. Load chat history
5. Hiển thị "Welcome back, [Name]!"
```

---

## 📝 CÀI ĐẶT

### **Bước 1: Cập nhật Database**
```bash
# Drop old database (nếu có data cũ)
mysql -u root -p
DROP DATABASE IF EXISTS voice_chat_db;

# Tạo database mới
mysql -u root -p < backend/database/schema.sql
```

### **Bước 2: Cập nhật Dependencies**
```bash
cd backend
pip install pillow  # For avatar upload
```

### **Bước 3: Tạo Folder Upload**
```bash
mkdir backend/uploads
mkdir backend/uploads/avatars
```

### **Bước 4: Cập nhật .env**
```env
# Avatar upload path
UPLOAD_FOLDER=uploads/avatars
MAX_AVATAR_SIZE=5242880  # 5MB
```

---

## 🎨 FRONTEND COMPONENTS

### **1. RegistrationModal.tsx**
Form đăng ký với:
- Avatar upload preview
- Input fields validation
- Gender radio buttons
- Age calculation từ birth year

### **2. SettingsModal.tsx**
Settings page với:
- View current profile
- Edit profile
- Change avatar
- Logout button

### **3. UserBadge Component**
Hiển thị trong sidebar:
```tsx
<div className="user-badge">
  <img src={avatar} />
  <div>
    <div className="name">{fullName}</div>
    <div className="username">@{username}</div>
  </div>
  <button onClick={openSettings}>⚙️</button>
</div>
```

---

## 🔧 BACKEND API

### **WebSocket Messages:**

#### **Client → Server:**

```javascript
// Check if user exists (auto on face detection)
{
  type: 'check_user',
  face_data: base64_image
}

// Register new user
{
  type: 'register_user',
  username: 'john_doe',
  full_name: 'John Doe',
  gender: 'male',
  birth_year: 1995,
  age: 29,
  avatar: base64_image,
  face_data: base64_image
}

// Update profile
{
  type: 'update_profile',
  user_id: 123,
  full_name: 'John Smith',
  gender: 'male',
  birth_year: 1995,
  age: 29,
  avatar: base64_image  // optional
}

// Get user profile
{
  type: 'get_profile',
  user_id: 123
}
```

#### **Server → Client:**

```javascript
// User check result
{
  type: 'user_check_result',
  exists: true,
  user: {
    id: 123,
    username: 'john_doe',
    full_name: 'John Doe',
    gender: 'male',
    age: 29,
    avatar_url: '/uploads/avatars/123.jpg'
  }
}

// Registration success
{
  type: 'registration_success',
  user_id: 123,
  message: 'Welcome, John!'
}

// Profile updated
{
  type: 'profile_updated',
  success: true
}
```

---

## 💾 FACE RECOGNITION FLOW

### **Cách Hoạt Động:**

1. **Capture Face:**
   - Frontend gửi frame từ webcam (hidden)
   - Backend extract face embedding

2. **Check Database:**
   - So sánh embedding với tất cả users
   - Tính cosine distance
   - Threshold: 0.6 (có thể điều chỉnh)

3. **Match Result:**
   - **Match found:** Auto login
   - **No match:** Show registration form

### **Code Example:**

```python
# backend/modules/face_recognition.py

def recognize_user(face_image_bytes, db):
    # Extract embedding
    embedding = extract_face_embedding(face_image_bytes)
    
    # Get all users
    users = db.get_all_users()
    
    # Find best match
    best_match = None
    best_distance = float('inf')
    
    for user in users:
        distance = cosine_distance(embedding, user['face_embedding'])
        if distance < best_distance:
            best_distance = distance
            best_match = user
    
    # Check threshold
    if best_distance < 0.6:  # Match found
        return best_match
    else:  # New user
        return None
```

---

## 🎯 FEATURES NÂNG CAO

### **1. Multi-Face Support**
- Phát hiện nhiều khuôn mặt
- Chọn khuôn mặt chính
- Cảnh báo nếu có nhiều người

### **2. Face Verification**
- Yêu cầu verify lại khuôn mặt
- Tăng security

### **3. Avatar Generation**
- Tự động crop khuôn mặt từ webcam
- Làm avatar mặc định

### **4. Profile Completion**
- Track % profile hoàn thiện
- Nhắc nhở cập nhật thông tin

---

## 🐛 TROUBLESHOOTING

### **Lỗi: Face not detected**
- Đảm bảo đủ ánh sáng
- Nhìn thẳng vào camera
- Khoảng cách phù hợp

### **Lỗi: Username already exists**
- Chọn username khác
- Hoặc login với username đó

### **Lỗi: Avatar upload failed**
- Check file size < 5MB
- Format: JPG, PNG
- Check folder permissions

---

## 📊 DATABASE QUERIES

### **Tạo User:**
```sql
INSERT INTO users (username, full_name, gender, birth_year, age, avatar_url, face_embedding)
VALUES ('john_doe', 'John Doe', 'male', 1995, 29, '/uploads/avatars/123.jpg', '[...]');
```

### **Get User Conversations:**
```sql
SELECT c.* FROM conversations c
WHERE c.user_id = 123
ORDER BY c.updated_at DESC;
```

### **Get User Stats:**
```sql
SELECT 
  u.username,
  COUNT(DISTINCT c.id) as total_conversations,
  COUNT(m.id) as total_messages
FROM users u
LEFT JOIN conversations c ON c.user_id = u.id
LEFT JOIN messages m ON m.conversation_id = c.id
WHERE u.id = 123
GROUP BY u.id;
```

---

## 🚀 NEXT STEPS

1. **Implement Registration Form** (Frontend)
2. **Update Face Recognition Module** (Backend)
3. **Add Avatar Upload Handler** (Backend)
4. **Create Settings Page** (Frontend)
5. **Test Full Flow**

---

**Bạn muốn tôi implement phần nào trước?**
- Registration Form (Frontend)
- Face Recognition với Database (Backend)
- Settings Page (Frontend)
- Tất cả cùng lúc
