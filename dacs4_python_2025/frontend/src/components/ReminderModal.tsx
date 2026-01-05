import { useState } from 'react';

interface Reminder {
  id: number;
  title: string;
  description?: string;
  reminder_time: string;
  is_completed: boolean;
}

interface ReminderModalProps {
  reminders: Reminder[];
  onClose: () => void;
  onCreateReminder: (data: { title: string; description: string; reminder_time: string }) => void;
  onCompleteReminder: (id: number) => void;
  onDeleteReminder: (id: number) => void;
}

export default function ReminderModal({ 
  reminders, 
  onClose, 
  onCreateReminder,
  onCompleteReminder,
  onDeleteReminder 
}: ReminderModalProps) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');

  const handleCreate = () => {
    if (!title || !date || !time) {
      alert('Please fill in all required fields');
      return;
    }

    const reminderTime = `${date} ${time}:00`;
    onCreateReminder({ title, description, reminder_time: reminderTime });
    
    // Reset form
    setTitle('');
    setDescription('');
    setDate('');
    setTime('');
    setShowCreateForm(false);
  };

  const formatDateTime = (datetime: string) => {
    const d = new Date(datetime);
    return d.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="reminder-modal-overlay" onClick={onClose}>
      <div className="reminder-modal" onClick={(e) => e.stopPropagation()}>
        <div className="reminder-header">
          <h2>🔔 AI Reminders</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="reminder-content">
          {!showCreateForm ? (
            <>
              <button 
                className="btn-primary create-reminder-btn" 
                onClick={() => setShowCreateForm(true)}
              >
                ➕ Create New Reminder
              </button>

              <div className="reminders-list">
                {reminders.length === 0 ? (
                  <div className="empty-state">
                    <p>📭 No reminders yet</p>
                    <p className="empty-hint">Create your first reminder to get AI voice notifications!</p>
                  </div>
                ) : (
                  reminders.map(reminder => (
                    <div key={reminder.id} className={`reminder-item ${reminder.is_completed ? 'completed' : ''}`}>
                      <div className="reminder-info">
                        <div className="reminder-title">{reminder.title}</div>
                        {reminder.description && (
                          <div className="reminder-desc">{reminder.description}</div>
                        )}
                        <div className="reminder-time">
                          🕐 {formatDateTime(reminder.reminder_time)}
                        </div>
                      </div>
                      <div className="reminder-actions">
                        {!reminder.is_completed && (
                          <button 
                            className="btn-complete"
                            onClick={() => onCompleteReminder(reminder.id)}
                            title="Mark as complete"
                          >
                            ✓
                          </button>
                        )}
                        <button 
                          className="btn-delete"
                          onClick={() => onDeleteReminder(reminder.id)}
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="create-reminder-form">
              <h3>Create New Reminder</h3>
              
              <div className="form-group">
                <label>Title *</label>
                <input
                  type="text"
                  placeholder="e.g., Team Meeting"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Description (optional)</label>
                <textarea
                  placeholder="Additional details..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="form-textarea"
                  rows={3}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Date *</label>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>Time *</label>
                  <input
                    type="time"
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-actions">
                <button className="btn-primary" onClick={handleCreate}>
                  ✅ Create Reminder
                </button>
                <button className="btn-secondary" onClick={() => setShowCreateForm(false)}>
                  ❌ Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
