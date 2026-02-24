import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import AskMode from './components/ask/AskMode';
import OnboardMode from './components/onboard/OnboardMode';
import ExploreMode from './components/explore/ExploreMode';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/ask" replace />} />
        <Route path="ask" element={<AskMode />} />
        <Route path="onboard" element={<OnboardMode />} />
        <Route path="explore" element={<ExploreMode />} />
      </Route>
    </Routes>
  );
}
