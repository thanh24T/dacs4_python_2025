interface ReminderNotificationProps {
  title: string;
  description?: string;
  onDismiss: () => void;
}

export default function ReminderNotification({ title, description, onDismiss }: ReminderNotificationProps) {
  return (
    <div className="reminder-notification-overlay">
      <div className="reminder-notification-modal">
        <div className="reminder-icon">🔔</div>
        <h2 className="reminder-notification-title">{title}</h2>
        {description && <p className="reminder-notification-desc">{description}</p>}
        <button className="reminder-dismiss-btn" onClick={onDismiss}>
          Got it!
        </button>
      </div>
    </div>
  );
}
