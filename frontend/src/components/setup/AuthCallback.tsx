import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, AlertCircle } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { authApi } from '../../lib/api';

export default function AuthCallback() {
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const ghError = params.get('error_description') || params.get('error');

    if (ghError) {
      setError(ghError);
      return;
    }

    if (!code) {
      setError('No authorization code received from GitHub');
      return;
    }

    authApi
      .callback(code)
      .then(() => refresh())
      .then(() => navigate('/setup', { replace: true }))
      .catch((err) => {
        setError(err.response?.data?.detail || err.message || 'Authentication failed');
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="glass-panel p-10 max-w-sm w-full text-center space-y-4">
        {error ? (
          <>
            <AlertCircle className="w-10 h-10 text-red-400 mx-auto" />
            <h2 className="text-lg font-semibold text-white">Authentication failed</h2>
            <p className="text-sm text-red-300">{error}</p>
            <button
              onClick={() => navigate('/setup', { replace: true })}
              className="text-sm text-brand-400 hover:text-brand-300 transition-colors"
            >
              Back to setup
            </button>
          </>
        ) : (
          <>
            <Loader2 className="w-8 h-8 text-brand-400 animate-spin mx-auto" />
            <p className="text-sm text-gray-400">Completing GitHub sign-in...</p>
          </>
        )}
      </div>
    </div>
  );
}
