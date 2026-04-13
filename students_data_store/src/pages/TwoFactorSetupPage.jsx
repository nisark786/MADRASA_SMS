import { useEffect, useState } from 'react';
import { Eye, EyeOff, Copy, Check } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function TwoFactorSetupPage() {
  const { user } = useAuthStore();
  const [state, setState] = useState('loading'); // loading, qr, confirm, success, error
  const [qrCode, setQrCode] = useState(null);
  const [secret, setSecret] = useState(null);
  const [totp, setTotp] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [copied, setCopied] = useState(false);
  const [backupCodes, setBackupCodes] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initiate2FA = async () => {
      try {
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/auth/2fa/setup`,
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
          setQrCode(data.qr_code);
          setSecret(data.secret);
          setState('qr');
        } else {
          setError(data.detail || 'Failed to initiate 2FA setup');
          setState('error');
        }
      } catch (err) {
        console.error('Error initiating 2FA:', err);
        setError('An error occurred while setting up 2FA');
        setState('error');
      }
    };

    initiate2FA();
  }, []);

  const handleCopySecret = () => {
    navigator.clipboard.writeText(secret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleConfirmSetup = async () => {
    if (!totp || totp.length !== 6 || !/^\d+$/.test(totp)) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/auth/2fa/setup/confirm`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ totp_code: totp }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setBackupCodes(data.backup_codes);
        setState('success');
      } else {
        setError(data.detail || 'Invalid code. Please try again.');
      }
    } catch (err) {
      console.error('Error confirming 2FA:', err);
      setError('An error occurred while confirming 2FA');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
        {state === 'loading' && (
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Setting up Two-Factor Authentication...</p>
          </div>
        )}

        {state === 'qr' && (
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Set Up 2FA</h1>
            <p className="text-gray-600 mb-6">
              Scan this QR code with an authenticator app like Google Authenticator, Microsoft Authenticator, or Authy.
            </p>

            {qrCode && (
              <div className="bg-gray-50 p-4 rounded-lg mb-6 flex justify-center">
                <img src={`data:image/png;base64,${qrCode}`} alt="2FA QR Code" className="w-48 h-48" />
              </div>
            )}

            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">Or enter this secret manually:</p>
              <div className="flex items-center justify-between">
                <code className="text-lg font-mono font-bold text-gray-900 break-all">
                  {showSecret ? secret : secret?.replace(/./g, '•')}
                </code>
                <button
                  onClick={() => setShowSecret(!showSecret)}
                  className="ml-2 p-1 hover:bg-gray-200 rounded"
                >
                  {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <button
                onClick={handleCopySecret}
                className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
              >
                {copied ? (
                  <>
                    <Check className="w-4 h-4 text-green-600" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    Copy Secret
                  </>
                )}
              </button>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter 6-digit code from your authenticator:
              </label>
              <input
                type="text"
                value={totp}
                onChange={(e) => setTotp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength="6"
                className="w-full px-4 py-2 text-center text-2xl font-mono tracking-widest border-2 border-gray-300 rounded-lg focus:border-indigo-600 focus:outline-none"
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            <button
              onClick={handleConfirmSetup}
              disabled={loading || totp.length !== 6}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Verifying...' : 'Verify & Enable 2FA'}
            </button>
          </div>
        )}

        {state === 'success' && (
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="bg-green-100 p-3 rounded-full">
                <Check className="w-8 h-8 text-green-600" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">2FA Enabled!</h1>
            <p className="text-gray-600 mb-6">
              Two-Factor Authentication is now active on your account. Save your backup codes below in a secure location.
            </p>

            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-left">
              <p className="text-sm font-semibold text-gray-900 mb-3">Backup Codes (Save These!):</p>
              <div className="grid grid-cols-2 gap-2">
                {backupCodes.map((code, idx) => (
                  <code
                    key={idx}
                    className="font-mono text-sm bg-white p-2 rounded border border-yellow-100 text-center text-gray-700"
                  >
                    {code}
                  </code>
                ))}
              </div>
              <p className="text-xs text-yellow-700 mt-3">
                Use these codes to access your account if you lose your authenticator.
              </p>
            </div>

            <a
              href="/profile"
              className="inline-block px-6 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
            >
              Return to Profile
            </a>
          </div>
        )}

        {state === 'error' && (
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <div className="bg-red-100 p-3 rounded-full">
                <span className="text-red-600 text-2xl">⚠</span>
              </div>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Setup Failed</h1>
            <p className="text-gray-600 mb-6">{error}</p>
            <a
              href="/profile"
              className="inline-block px-6 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors"
            >
              Back to Profile
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
