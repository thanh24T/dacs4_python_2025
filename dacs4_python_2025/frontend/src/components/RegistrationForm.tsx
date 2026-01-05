import { useState, useRef } from 'react';

interface RegistrationFormProps {
  onRegister: (data: RegistrationData) => void;
  onCancel: () => void;
}

interface RegistrationData {
  username: string;
  fullName: string;
  gender: 'male' | 'female' | 'other';
  birthYear: number;
  age: number;
  avatar?: string; // base64
}

function RegistrationForm({ onRegister, onCancel }: RegistrationFormProps) {
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [gender, setGender] = useState<'male' | 'female' | 'other'>('other');
  const [birthYear, setBirthYear] = useState('');
  const [age, setAge] = useState('');
  const [avatar, setAvatar] = useState<string>('');
  const [avatarPreview, setAvatarPreview] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('Avatar size must be less than 5MB');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        setAvatar(base64);
        setAvatarPreview(base64);
      };
      reader.readAsDataURL(file);
    }
  };

  const calculateAge = (year: string) => {
    if (year && !isNaN(parseInt(year))) {
      const currentYear = new Date().getFullYear();
      const calculatedAge = currentYear - parseInt(year);
      if (calculatedAge > 0 && calculatedAge < 150) {
        setAge(calculatedAge.toString());
      }
    }
  };

  const handleBirthYearChange = (value: string) => {
    setBirthYear(value);
    calculateAge(value);
  };

  const handleSubmit = () => {
    // Validation
    if (!username.trim()) {
      alert('Please enter a username');
      return;
    }
    if (!fullName.trim()) {
      alert('Please enter your full name');
      return;
    }
    if (!birthYear || isNaN(parseInt(birthYear))) {
      alert('Please enter a valid birth year');
      return;
    }

    const data: RegistrationData = {
      username: username.trim(),
      fullName: fullName.trim(),
      gender,
      birthYear: parseInt(birthYear),
      age: parseInt(age) || 0,
      avatar: avatar || undefined
    };

    onRegister(data);
  };

  return (
    <div className="registration-modal-overlay">
      <div className="registration-modal">
        <h2>Welcome! Let's Get Started 🎉</h2>
        <p className="subtitle">Create your profile to continue</p>

        {/* Avatar Upload */}
        <div className="avatar-section">
          <div 
            className="avatar-preview" 
            onClick={() => fileInputRef.current?.click()}
          >
            {avatarPreview ? (
              <img src={avatarPreview} alt="Avatar" />
            ) : (
              <div className="avatar-placeholder">
                <span>📷</span>
                <span>Upload Avatar</span>
              </div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleAvatarChange}
            style={{ display: 'none' }}
          />
        </div>

        {/* Form Fields */}
        <div className="form-group">
          <label>Full Name *</label>
          <input
            type="text"
            placeholder="John Doe"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Username *</label>
          <input
            type="text"
            placeholder="john_doe"
            value={username}
            onChange={(e) => setUsername(e.target.value.toLowerCase().replace(/\s/g, '_'))}
          />
        </div>

        <div className="form-group">
          <label>Gender</label>
          <div className="gender-options">
            <label className="radio-label">
              <input
                type="radio"
                value="male"
                checked={gender === 'male'}
                onChange={(e) => setGender(e.target.value as 'male')}
              />
              <span>Male</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                value="female"
                checked={gender === 'female'}
                onChange={(e) => setGender(e.target.value as 'female')}
              />
              <span>Female</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                value="other"
                checked={gender === 'other'}
                onChange={(e) => setGender(e.target.value as 'other')}
              />
              <span>Other</span>
            </label>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Birth Year *</label>
            <input
              type="number"
              placeholder="1995"
              value={birthYear}
              onChange={(e) => handleBirthYearChange(e.target.value)}
              min="1900"
              max={new Date().getFullYear()}
            />
          </div>
          <div className="form-group">
            <label>Age</label>
            <input
              type="number"
              placeholder="29"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              readOnly
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="form-buttons">
          <button className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleSubmit}>
            Register
          </button>
        </div>
      </div>
    </div>
  );
}

export default RegistrationForm;
