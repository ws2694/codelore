import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { MessageCircle, GraduationCap, GitBranch, Activity, Database, GitFork } from 'lucide-react';
import { useEffect, useState } from 'react';
import { healthApi } from '../../lib/api';
import { useAuth } from '../../hooks/useAuth';
import type { HealthStatus } from '../../lib/types';

const NAV_ITEMS = [
  { name: 'Ask', path: '/ask', icon: MessageCircle, desc: 'Q&A about your codebase' },
  { name: 'Onboard', path: '/onboard', icon: GraduationCap, desc: 'Guided learning paths' },
  { name: 'Explore', path: '/explore', icon: GitBranch, desc: 'Timeline & archaeology' },
];

export default function MainLayout() {
  const location = useLocation();
  const { auth } = useAuth();
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    healthApi.check().then(setHealth).catch(() => {});
  }, []);

  const totalDocs = health
    ? Object.values(health.indices).reduce((sum, n) => sum + Math.max(n, 0), 0)
    : 0;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900/80 border-r border-gray-800/50 flex flex-col shrink-0">
        {/* Logo */}
        <div className="p-5 border-b border-gray-800/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm">
              CL
            </div>
            <div>
              <h1 className="font-semibold text-white text-base">CodeLore</h1>
              <p className="text-[11px] text-gray-500">Codebase Memory Agent</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm ${
                  isActive
                    ? 'bg-brand-600/20 text-brand-300 border border-brand-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <div>
                  <span className="font-medium">{item.name}</span>
                  <p className="text-[10px] text-gray-500 mt-0.5">{item.desc}</p>
                </div>
              </NavLink>
            );
          })}
        </nav>

        {/* Connected repo */}
        {auth?.selected_repo && (
          <div className="px-4 py-3 border-t border-gray-800/50">
            <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
              <GitFork className="w-3 h-3" />
              <span className="text-gray-500">Connected repo</span>
            </div>
            <p className="text-sm text-white font-medium truncate">{auth.selected_repo}</p>
            {auth.user && (
              <p className="text-[10px] text-gray-500 mt-0.5">@{auth.user}</p>
            )}
            <NavLink
              to="/setup"
              className="text-[10px] text-brand-400 hover:text-brand-300 mt-1 inline-block"
            >
              Switch repo
            </NavLink>
          </div>
        )}

        {/* Status footer */}
        <div className="p-4 border-t border-gray-800/50 space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <Database className="w-3 h-3 text-gray-500" />
            <span className="text-gray-500">Elasticsearch</span>
            <span className={`ml-auto w-1.5 h-1.5 rounded-full ${
              health?.elasticsearch ? 'bg-green-400' : 'bg-red-400'
            }`} />
          </div>
          {health?.elasticsearch && (
            <div className="flex items-center gap-2 text-xs">
              <Activity className="w-3 h-3 text-gray-500" />
              <span className="text-gray-500">{totalDocs.toLocaleString()} documents indexed</span>
            </div>
          )}
          {health && Object.entries(health.indices).map(([idx, count]) => (
            <div key={idx} className="flex items-center justify-between text-[10px] text-gray-600 pl-5">
              <span>{idx.replace('codelore-', '')}</span>
              <span>{count >= 0 ? count : 'N/A'}</span>
            </div>
          ))}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
