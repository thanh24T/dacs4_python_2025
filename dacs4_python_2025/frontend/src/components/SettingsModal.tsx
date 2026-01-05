import { useState } from 'react';

interface User {
  id: number;
  username: string;
  full_name: string;
  gender: string;
  age: number;
  avatar_url?: string;
}

interface SettingsModalProps {
  user: User;
  onClose: () => void;
  onLogout?: () => void;
  onUpdateProfile?: (data: Partial<User>) => void;
}

export default function SettingsModal({ user, onClose, onLogout, onUpdateProfile }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState<'profile' | 'preferences'>('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    full_name: user.full_name,
    gender: user.gender,
    age: user.age
  });
  const [selectedSpeaker, setSelectedSpeaker] = useState('NM1'); // Default speaker

  const handleSave = () => {
    if (onUpdateProfile) {
      onUpdateProfile(editData);
    }
    setIsEditing(false);
  };

  const speakers = [
    { id: 'NM1', name: 'Male Voice 1', gender: 'male' },
    { id: 'NM2', name: 'Male Voice 2', gender: 'male' },
    { id: 'NF', name: 'Female Voice', gender: 'female' },
    { id: 'SM', name: 'Southern Male', gender: 'male' },
    { id: 'SF', name: 'Southern Female', gender: 'female' }
  ];

  return (
    <div className="settings-modal-overlay" onClick={onClose}>
      <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>⚙️ Settings</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="settings-tabs">
          <button 
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            👤 Profile
          </button>
          <button 
            className={`tab-btn ${activeTab === 'preferences' ? 'active' : ''}`}
            onClick={() => setActiveTab('preferences')}
          >
            🎨 Preferences
          </button>
        </div>

        <div className="settings-content">
          {activeTab === 'profile' && (
            <div className="profile-section">
              <div className="profile-avatar-large">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt={user.username} />
                ) : (
                  <div className="avatar-placeholder-large">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>

              <div className="profile-info">
                {isEditing ? (
                  <>
                    <div className="info-row">
                      <span className="info-label">Full Name</span>
                      <input 
                        type="text" 
                        value={editData.full_name}
                        onChange={(e) => setEditData({...editData, full_name: e.target.value})}
                        className="edit-input"
                      />
                    </div>
                    <div className="info-row">
                      <span className="info-label">Gender</span>
                      <select 
                        value={editData.gender}
                        onChange={(e) => setEditData({...editData, gender: e.target.value})}
                        className="edit-input"
                      >
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Age</span>
                      <input 
                        type="number" 
                        value={editData.age}
                        onChange={(e) => setEditData({...editData, age: parseInt(e.target.value)})}
                        className="edit-input"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="info-row">
                      <span className="info-label">Full Name</span>
                      <span className="info-value">{user.full_name}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Username</span>
                      <span className="info-value">@{user.username}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Gender</span>
                      <span className="info-value">{user.gender}</span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Age</span>
                      <span className="info-value">{user.age} years old</span>
                    </div>
                  </>
                )}
              </div>

              <div className="profile-actions">
                {isEditing ? (
                  <>
                    <button className="btn-primary" onClick={handleSave}>
                      ✅ Save Changes
                    </button>
                    <button className="btn-secondary" onClick={() => setIsEditing(false)}>
                      ❌ Cancel
                    </button>
                  </>
                ) : (
                  <button className="btn-secondary" onClick={() => setIsEditing(true)}>
                    ✏️ Edit Profile
                  </button>
                )}
                {onLogout && (
                  <button className="btn-danger" onClick={onLogout}>
                    🚪 Logout
                  </button>
                )}
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="preferences-section">
              <div className="pref-group">
                <h3>🎤 Voice Settings</h3>
                
                <div className="pref-item">
                  <label>AI Voice Speaker</label>
                  <select 
                    value={selectedSpeaker}
                    onChange={(e) => setSelectedSpeaker(e.target.value)}
                    className="speaker-select"
                  >
                    {speakers.map(speaker => (
                      <option key={speaker.id} value={speaker.id}>
                        {speaker.name}
                      </option>
                    ))}
                  </select>
                  <span className="pref-note">Choose AI voice personality</span>
                </div>

                <div className="pref-item">
                  <label>Voice Speed</label>
                  <input type="range" min="0.5" max="2" step="0.1" defaultValue="1" disabled />
                  <span className="pref-note">Coming soon</span>
                </div>
              </div>

              <div className="pref-group">
                <h3>🎨 Appearance</h3>
                <div className="pref-item">
                  <label>Theme</label>
                  <select disabled>
                    <option>Dark (Default)</option>
                    <option>Light</option>
                  </select>
                  <span className="pref-note">Coming soon</span>
                </div>
              </div>

              <div className="pref-group">
                <h3>🔔 Notifications</h3>
                <div className="pref-item">
                  <label>
                    <input type="checkbox" disabled />
                    Enable sound notifications
                  </label>
                  <span className="pref-note">Coming soon</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
