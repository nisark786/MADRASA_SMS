import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function ResendVerificationPage() {
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const [state, setState] = useState('idle'); // idle, loading, success, error
  const [message, setMessage] = useState('');

  const handleResendEmail = async () => {
    if (!user) {
      setMessage('You must be logged in to resend verification email.');
      setState('error');
      return;
    }

    setState('loading');
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/auth/resend-verification-email`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
        }
      );

      const data = await response.json();

      if (response.ok) {
        setState('success');
        setMessage(data.message);
      } else {
        setState('error');
        setMessage(data.detail || 'Failed to resend verification email. Please try again.');
      }
    } catch (error) {
      console.error('Error resending email:', error);
      setState('error');
      setMessage('An error occurred. Please try again later.');
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" strokeWidth={1.5} />
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Not Logged In</h1>
            <p className="text-gray-600 mb-6">You must be logged in to resend verification email.</p>
            <button
              onClick={() => navigate('/login')}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center">
          {state !== 'success' && (
            <>
              <div className="flex justify-center mb-4">
                <div className="bg-indigo-100 p-3 rounded-full">
                  <Mail className="w-8 h-8 text-indigo-600" strokeWidth={2} />
                </div>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Resend Verification Email</h1>
              <p className="text-gray-600 mb-4">
                If you didn't receive the verification email, we can send it again to:
              </p>
              <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
                <p className="text-sm font-semibold text-gray-900">{user.email}</p>
                <p className="text-xs text-gray-600 mt-1">
                  {user.first_name} {user.last_name}
                </p>
              </div>

              {message && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-700">{message}</p>
                </div>
              )}

              <button
                onClick={handleResendEmail}
                disabled={state === 'loading'}
                className="w-full px-4 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {state === 'loading' ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Sending...
                  </>
                ) : (
                  'Resend Verification Email'
                )}
              </button>

              <button
                onClick={() => navigate('/dashboard')}
                className="w-full mt-3 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
              >
                Back to Dashboard
              </button>
            </>
          )}

          {state === 'success' && (
            <>
              <div className="flex justify-center mb-4">
                <CheckCircle className="w-16 h-16 text-green-500" strokeWidth={1.5} />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Email Sent!</h1>
              <p className="text-gray-600 mb-4">{message}</p>
              <p className="text-sm text-gray-600 mb-6">
                Please check your inbox and click the verification link.
              </p>
              <button
                onClick={() => navigate('/dashboard')}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
              >
                Return to Dashboard
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
