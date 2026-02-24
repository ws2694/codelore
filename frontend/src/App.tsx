import { Routes, Route, Navigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import MainLayout from './components/layout/MainLayout';
import AskMode from './components/ask/AskMode';
import OnboardMode from './components/onboard/OnboardMode';
import ExploreMode from './components/explore/ExploreMode';
import SetupPage from './components/setup/SetupPage';
import AuthCallback from './components/setup/AuthCallback';
import { useAuth } from './hooks/useAuth';

export default function App() {
  const { auth, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-brand-400 animate-spin" />
      </div>
    );
  }

  const needsSetup = !auth?.authenticated || !auth?.selected_repo;

  return (
    <Routes>
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/setup" element={<SetupPage />} />

      <Route
        path="/"
        element={needsSetup ? <Navigate to="/setup" replace /> : <MainLayout />}
      >
        <Route index element={<Navigate to="/ask" replace />} />
        <Route path="ask" element={<AskMode />} />
        <Route path="onboard" element={<OnboardMode />} />
        <Route path="explore" element={<ExploreMode />} />
      </Route>

      <Route path="*" element={<Navigate to={needsSetup ? '/setup' : '/ask'} replace />} />
    </Routes>
  );
}
