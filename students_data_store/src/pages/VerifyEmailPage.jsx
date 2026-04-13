import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function VerifyEmailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { logout } = useAuthStore();

  const [state, setState] = useState('loading'); // loading, success, error
  const [message, setMessage] = useState('');
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setState('error');
      setMessage('No verification token provided. Please check your email link.');
      return;
    }

    const verifyEmail = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/auth/verify-email/${token}`,
          { method: 'POST' }
        );

        const data = await response.json();

        if (response.ok) {
          setState('success');
          setMessage(data.message);
          setUserInfo(data.user);

          // Redirect to login after 3 seconds
          setTimeout(() => {
            // Logout and redirect to login
            logout();
            navigate('/login', {
              state: { message: 'Email verified! Please log in with your credentials.' }
            });
          }, 3000);
        } else {
          setState('error');
          setMessage(data.detail || 'Email verification failed. Please try again.');
        }
      } catch (error) {
        console.error('Verification error:', error);
        setState('error');
        setMessage('An error occurred during email verification. Please try again.');
      }
    };

    verifyEmail();
  }, [searchParams, navigate, logout]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center">
          {state === 'loading' && (
            <>
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Verifying Email</h1>
              <p className="text-gray-600">Please wait while we verify your email address...</p>
            </>
          )}

          {state === 'success' && (
            <>
              <div className="flex justify-center mb-4">
                <CheckCircle className="w-16 h-16 text-green-500" strokeWidth={1.5} />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Email Verified!</h1>
              <p className="text-gray-600 mb-4">{message}</p>
              {userInfo && (
                <div className="bg-indigo-50 rounded-lg p-4 text-left mb-4">
                  <p className="text-sm text-gray-700">
                    <strong>Welcome,</strong> {userInfo.first_name || userInfo.username}!
                  </p>
                  <p className="text-xs text-gray-600 mt-1">{userInfo.email}</p>
                </div>
              )}
              <p className="text-sm text-gray-500">Redirecting to login in a few seconds...</p>
            </>
          )}

          {state === 'error' && (
            <>
              <div className="flex justify-center mb-4">
                <AlertCircle className="w-16 h-16 text-red-500" strokeWidth={1.5} />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Verification Failed</h1>
              <p className="text-gray-600 mb-6">{message}</p>
              <button
                onClick={() => navigate('/login')}
                className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
              >
                Back to Login
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
