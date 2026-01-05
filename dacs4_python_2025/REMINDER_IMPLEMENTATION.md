# AI Reminder System - Implementation Complete

## ✅ Completed Components:

### 1. Database Schema
- ✅ Table `reminders` created with fields:
  - id, user_id, title, description
  - reminder_time, is_completed, is_notified
  - created_at, updated_at

### 2. Backend Modules
- ✅ `modules/database.py` - Reminder CRUD operations
- ✅ `modules/reminder_scheduler.py` - Background scheduler

### 3. Frontend Components
- ✅ `ReminderModal.tsx` - UI for creating/managing reminders

## 🔧 Integration Steps:

### Step 1: Add Reminder Handlers to Server

Add these handlers in `server_rag.py` after the existing message handlers:

```python
# ========== REMINDER MANAGEMENT ==========
elif cmd_type == 'create_reminder':
    user_id = state.get('current_user_id')
    if user_id:
        title = data.get('title')
        description = data.get('description', '')
        reminder_time = data.get('reminder_time')
        
        reminder_id = db.create_reminder(user_id, title, reminder_time, description)
        
        if reminder_id:
            await websocket.send(json.dumps({
                'type': 'reminder_created',
                'reminder_id': reminder_id
            }))
            
            # Send updated reminders list
            reminders = db.get_reminders(user_id)
            await websocket.send(json.dumps({
                'type': 'reminders',
                'reminders': [
                    {
                        'id': r['id'],
                        'title': r['title'],
                        'description': r['description'],
                        'reminder_time': r['reminder_time'].isoformat() if hasattr(r['reminder_time'], 'isoformat') else str(r['reminder_time']),
                        'is_completed': r['is_completed']
                    }
                    for r in reminders
                ]
            }))

elif cmd_type == 'get_reminders':
    user_id = state.get('current_user_id')
    if user_id:
        reminders = db.get_reminders(user_id)
        await websocket.send(json.dumps({
            'type': 'reminders',
            'reminders': [
                {
                    'id': r['id'],
                    'title': r['title'],
                    'description': r['description'],
                    'reminder_time': r['reminder_time'].isoformat() if hasattr(r['reminder_time'], 'isoformat') else str(r['reminder_time']),
                    'is_completed': r['is_completed']
                }
                for r in reminders
            ]
        }))

elif cmd_type == 'complete_reminder':
    reminder_id = data.get('reminder_id')
    if reminder_id:
        db.complete_reminder(reminder_id)
        await websocket.send(json.dumps({
            'type': 'reminder_completed',
            'reminder_id': reminder_id
        }))

elif cmd_type == 'delete_reminder':
    reminder_id = data.get('reminder_id')
    if reminder_id:
        db.delete_reminder(reminder_id)
        await websocket.send(json.dumps({
            'type': 'reminder_deleted',
            'reminder_id': reminder_id
        }))
```

### Step 2: Add Reminder Callback

Add this function before `socket_handler`:

```python
async def reminder_callback(reminder):
    """Callback when reminder is due - send notification via WebSocket"""
    user_id = reminder['user_id']
    
    # Check if user is connected
    if user_id in active_connections:
        websocket = active_connections[user_id]
        
        try:
            # Send reminder notification
            message = f"Hey! It's time for: {reminder['title']}"
            if reminder['description']:
                message += f". {reminder['description']}"
            
            await websocket.send(json.dumps({
                'type': 'reminder_notification',
                'reminder': {
                    'id': reminder['id'],
                    'title': reminder['title'],
                    'description': reminder['description']
                },
                'message': message
            }))
            
            # Generate TTS
            loop = asyncio.get_running_loop()
            wav_bytes = await loop.run_in_executor(None, tts.generate_audio_bytes, message)
            
            if wav_bytes:
                await websocket.send(json.dumps({"type": "audio", "content": "audio_data"}))
                await websocket.send(wav_bytes)
            
            print(colorama.Fore.GREEN + f"[REMINDER] ✅ Notified user #{user_id}: {reminder['title']}" + colorama.Style.RESET_ALL)
            
        except Exception as e:
            print(colorama.Fore.RED + f"[REMINDER] Error sending notification: {e}" + colorama.Style.RESET_ALL)
```

### Step 3: Track Active Connections

In `socket_handler`, add:

```python
async def socket_handler(websocket):
    """Xử lý WebSocket connection"""
    print(colorama.Fore.GREEN + f"\n[WebSocket] Client connected!" + colorama.Style.RESET_ALL)
    
    # ... existing code ...
    
    # Track connection
    user_id = state.get('current_user_id')
    if user_id:
        active_connections[user_id] = websocket
    
    try:
        # ... existing gather code ...
    finally:
        # Remove from active connections
        if user_id and user_id in active_connections:
            del active_connections[user_id]
```

### Step 4: Start Scheduler

Add at the end of `server_rag.py`:

```python
async def main():
    """Main server function"""
    # Set reminder callback
    reminder_scheduler.set_callback(reminder_callback)
    
    # Start scheduler in background
    scheduler_task = asyncio.create_task(reminder_scheduler.start())
    
    # Start WebSocket server
    async with websockets.serve(socket_handler, "0.0.0.0", 8765):
        print(colorama.Fore.GREEN + "\n🚀 Server running on ws://0.0.0.0:8765" + colorama.Style.RESET_ALL)
        print(colorama.Fore.CYAN + "📡 Reminder scheduler active" + colorama.Style.RESET_ALL)
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(colorama.Fore.YELLOW + "\n\n👋 Server stopped" + colorama.Style.RESET_ALL)
        reminder_scheduler.stop()
```

## 🎨 Frontend Integration:

Add to `App.tsx`:

```typescript
const [showReminders, setShowReminders] = useState(false);
const [reminders, setReminders] = useState<Reminder[]>([]);

// Add reminder button in sidebar
<button className="reminder-btn" onClick={() => {
  // Request reminders from server
  if (socketRef.current && currentUser) {
    socketRef.current.send(JSON.stringify({ type: 'get_reminders' }));
  }
  setShowReminders(true);
}}>
  🔔 Reminders
</button>

// Handle reminder messages
else if (data.type === 'reminders') {
  setReminders(data.reminders);
} else if (data.type === 'reminder_notification') {
  // Show notification
  alert(`🔔 Reminder: ${data.message}`);
}

// Render modal
{showReminders && (
  <ReminderModal
    reminders={reminders}
    onClose={() => setShowReminders(false)}
    onCreateReminder={(data) => {
      socketRef.current?.send(JSON.stringify({
        type: 'create_reminder',
        ...data
      }));
    }}
    onCompleteReminder={(id) => {
      socketRef.current?.send(JSON.stringify({
        type: 'complete_reminder',
        reminder_id: id
      }));
    }}
    onDeleteReminder={(id) => {
      socketRef.current?.send(JSON.stringify({
        type: 'delete_reminder',
        reminder_id: id
      }));
    }}
  />
)}
```

## 🎨 CSS Styling:

Add to `index.css`:

```css
/* REMINDER MODAL */
.reminder-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.reminder-modal {
  background: #1a1a1a;
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.reminder-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reminder-content {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.create-reminder-btn {
  width: 100%;
  margin-bottom: 20px;
}

.reminders-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reminder-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(var(--orb-color), 0.2);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.3s ease;
}

.reminder-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgb(var(--orb-color));
}

.reminder-item.completed {
  opacity: 0.5;
  text-decoration: line-through;
}

.reminder-info {
  flex: 1;
}

.reminder-title {
  font-size: 16px;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
}

.reminder-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8px;
}

.reminder-time {
  font-size: 13px;
  color: rgb(var(--orb-color));
}

.reminder-actions {
  display: flex;
  gap: 8px;
}

.btn-complete, .btn-delete {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-complete:hover {
  background: rgba(0, 255, 0, 0.1);
  border-color: rgba(0, 255, 0, 0.3);
}

.btn-delete:hover {
  background: rgba(255, 0, 0, 0.1);
  border-color: rgba(255, 0, 0, 0.3);
}

.create-reminder-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.form-input, .form-textarea {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(var(--orb-color), 0.3);
  border-radius: 8px;
  padding: 12px;
  color: white;
  font-size: 14px;
}

.form-input:focus, .form-textarea:focus {
  outline: none;
  border-color: rgb(var(--orb-color));
  background: rgba(255, 255, 255, 0.08);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.5);
}

.empty-hint {
  font-size: 14px;
  margin-top: 8px;
}
```

## 🚀 Testing:

1. Run `python setup_database.py` to create reminders table
2. Start server: `python server_rag.py`
3. Create a reminder for 1 minute from now
4. Wait and see AI voice notification!

## 📝 Features:

- ✅ Create reminders with title, description, date/time
- ✅ View all reminders
- ✅ Mark as complete
- ✅ Delete reminders
- ✅ Real-time AI voice notifications via WebSocket
- ✅ Background scheduler checks every 30 seconds
- ✅ TTS announcement when reminder is due
