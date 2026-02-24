import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { authApi } from '../lib/api';
import type { AuthStatus } from '../lib/types';

interface AuthContextValue {
  auth: AuthStatus | null;
  isLoading: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export function useAuthProvider() {
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const status = await authApi.status();
      setAuth(status);
    } catch {
      setAuth({
        authenticated: false,
        method: null,
        user: null,
        avatar_url: null,
        selected_repo: null,
        oauth_configured: false,
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    await refresh();
  }, [refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { auth, isLoading, refresh, logout };
}
