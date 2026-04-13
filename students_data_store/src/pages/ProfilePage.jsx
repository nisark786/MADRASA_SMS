import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { API_BASE_URL } from '../api/config';
import Sidebar from '../components/layout/Sidebar';
import { User, Mail, Edit2, Lock, Eye, EyeOff, CheckCircle, AlertCircle, Save, X } from 'lucide-react';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user: authUser } = useAuthStore();

  // Profile state
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Edit profile state
  const [editingProfile, setEditingProfile] = useState(false);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
  });
  const [profileError, setProfileError] = useState(null);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  // Change password state
  const [editingPassword, setEditingPassword] = useState(false);
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordError, setPasswordError] = useState(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  // Load profile on mount
  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const token = localStorage.getItem('access_token');

      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load profile');
      }

      const data = await response.json();
      setProfile(data);
      setFormData({
        first_name: data.first_name || '',
        last_name: data.last_name || '',
        email: data.email || '',
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const checkPasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 12) strength += 1;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 1;
    if (/\d/.test(password)) strength += 1;
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) strength += 1;
    setPasswordStrength(strength);
  };

  const handlePasswordChange = (e) => {
    const password = e.target.value;
    setPasswordForm({ ...passwordForm, new_password: password });
    checkPasswordStrength(password);
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(false);
    setSavingProfile(true);

    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to update profile');
      }

      setProfile(data.user);
      setProfileSuccess(true);
      setEditingProfile(false);
      setTimeout(() => setProfileSuccess(false), 5000);
    } catch (err) {
      setProfileError(err.message);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    // Validate passwords match
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('Passwords do not match');
      return;
    }

    // Validate password strength
    if (passwordStrength < 4) {
      setPasswordError('Password does not meet security requirements');
      return;
    }

    setSavingPassword(true);

    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch(`${API_BASE_URL}/auth/profile/change-password`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(passwordForm),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to change password');
      }

      setPasswordSuccess(true);
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      setEditingPassword(false);
      setPasswordStrength(0);
      setTimeout(() => setPasswordSuccess(false), 5000);
    } catch (err) {
      setPasswordError(err.message);
    } finally {
      setSavingPassword(false);
    }
  };

  const getPasswordStrengthColor = () => {
    switch (passwordStrength) {
      case 0:
      case 1:
        return 'bg-red-500';
      case 2:
        return 'bg-yellow-500';
      case 3:
        return 'bg-blue-500';
      case 4:
        return 'bg-green-500';
      default:
        return 'bg-gray-300';
    }
  };

  const getPasswordStrengthText = () => {
    switch (passwordStrength) {
      case 0:
      case 1:
        return 'Weak';
      case 2:
        return 'Fair';
      case 3:
        return 'Good';
      case 4:
        return 'Strong';
      default:
        return 'N/A';
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gray-50/50 font-sans">
        <Sidebar />
        <main className="flex-1 p-8 md:p-12 overflow-y-auto min-w-0 flex items-center justify-center">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-100 mb-4">
              <div className="w-6 h-6 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
            </div>
            <p className="text-gray-600 font-medium">Loading profile...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50/50 font-sans">
      <Sidebar />
      <main className="flex-1 p-8 md:p-12 overflow-y-auto min-w-0">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="flex items-start justify-between mb-8">
            <div>
              <div className="flex items-center gap-2.5 mb-2">
                <div className="bg-indigo-600 p-2 rounded-xl">
                  <User className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-gray-900 leading-tight tracking-tight">My Profile</h1>
              </div>
              <p className="text-sm text-gray-500 font-medium ml-1">
                Manage your account settings and preferences
              </p>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700 font-medium">{error}</p>
            </div>
          )}

          {/* Success Messages */}
          {profileSuccess && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-green-700 font-medium">Profile updated successfully!</p>
            </div>
          )}

          {passwordSuccess && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-green-700 font-medium">Password changed successfully!</p>
            </div>
          )}

          {/* Profile Information Card */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm mb-6">
            <div className="flex items-start justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900">Profile Information</h2>
              {!editingProfile && (
                <button
                  onClick={() => setEditingProfile(true)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <Edit2 className="w-5 h-5 text-gray-600" />
                </button>
              )}
            </div>

            {editingProfile ? (
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                {profileError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-700 font-medium">{profileError}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">First Name</label>
                    <input
                      type="text"
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="First name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Last Name</label>
                    <input
                      type="text"
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Last name"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="your@email.com"
                    />
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    disabled={savingProfile}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" />
                    {savingProfile ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingProfile(false);
                      setProfileError(null);
                      setFormData({
                        first_name: profile.first_name || '',
                        last_name: profile.last_name || '',
                        email: profile.email || '',
                      });
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                  >
                    <X className="w-4 h-4" />
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500 font-medium mb-1">First Name</p>
                  <p className="text-base text-gray-900">{profile.first_name || '—'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium mb-1">Last Name</p>
                  <p className="text-base text-gray-900">{profile.last_name || '—'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium mb-1">Email Address</p>
                  <p className="text-base text-gray-900">{profile.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium mb-1">Username</p>
                  <p className="text-base text-gray-900">{profile.username}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-medium mb-1">Member Since</p>
                  <p className="text-base text-gray-900">{new Date(profile.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            )}
          </div>

          {/* Change Password Card */}
          <div className="bg-white rounded-lg border border-gray-200 p-6 shadow-sm">
            <div className="flex items-start justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Lock className="w-5 h-5 text-indigo-600" />
                Change Password
              </h2>
            </div>

            {editingPassword ? (
              <form onSubmit={handleChangePassword} className="space-y-4">
                {passwordError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-700 font-medium">{passwordError}</p>
                  </div>
                )}

                {/* Current Password */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Current Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type={showCurrentPassword ? 'text' : 'password'}
                      required
                      value={passwordForm.current_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                      className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Enter current password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showCurrentPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* New Password */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type={showNewPassword ? 'text' : 'password'}
                      required
                      value={passwordForm.new_password}
                      onChange={handlePasswordChange}
                      className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Enter new password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>

                  {/* Password Strength */}
                  {passwordForm.new_password && (
                    <div className="mt-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-gray-600">Strength:</span>
                        <span className="text-xs font-semibold text-gray-700">{getPasswordStrengthText()}</span>
                      </div>
                      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getPasswordStrengthColor()} transition-all`}
                          style={{ width: `${(passwordStrength / 4) * 100}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Password Requirements */}
                  <div className="mt-3 text-xs text-gray-600 space-y-1">
                    <div className={passwordForm.new_password.length >= 12 ? 'text-green-600 font-medium' : ''}>
                      {passwordForm.new_password.length >= 12 ? '✓' : '○'} At least 12 characters
                    </div>
                    <div className={/[a-z]/.test(passwordForm.new_password) && /[A-Z]/.test(passwordForm.new_password) ? 'text-green-600 font-medium' : ''}>
                      {/[a-z]/.test(passwordForm.new_password) && /[A-Z]/.test(passwordForm.new_password) ? '✓' : '○'} Uppercase and lowercase letters
                    </div>
                    <div className={/\d/.test(passwordForm.new_password) ? 'text-green-600 font-medium' : ''}>
                      {/\d/.test(passwordForm.new_password) ? '✓' : '○'} At least one number
                    </div>
                    <div className={/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(passwordForm.new_password) ? 'text-green-600 font-medium' : ''}>
                      {/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(passwordForm.new_password) ? '✓' : '○'} Special character
                    </div>
                  </div>
                </div>

                {/* Confirm Password */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm New Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type={showConfirmPassword ? 'text' : 'password'}
                      required
                      value={passwordForm.confirm_password}
                      onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                      className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Confirm new password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>

                  {passwordForm.confirm_password && (
                    <div className="mt-2">
                      {passwordForm.new_password === passwordForm.confirm_password ? (
                        <p className="text-xs text-green-600 font-medium">✓ Passwords match</p>
                      ) : (
                        <p className="text-xs text-red-600 font-medium">✕ Passwords do not match</p>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    disabled={savingPassword || passwordStrength < 4}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50"
                  >
                    <Lock className="w-4 h-4" />
                    {savingPassword ? 'Changing...' : 'Change Password'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditingPassword(false);
                      setPasswordError(null);
                      setPasswordForm({
                        current_password: '',
                        new_password: '',
                        confirm_password: '',
                      });
                      setPasswordStrength(0);
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
                  >
                    <X className="w-4 h-4" />
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  Update your password to keep your account secure. We recommend using a strong, unique password.
                </p>
                <button
                  onClick={() => setEditingPassword(true)}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
                >
                  Change Password
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
