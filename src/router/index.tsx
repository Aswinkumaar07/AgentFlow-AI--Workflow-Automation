import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '../lib/react-query';

import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { SignupPage } from '../pages/SignupPage';
import { RegisterPage } from '../pages/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage';
import { WorkflowBuilderPage } from '../pages/WorkflowBuilderPage';
import { WorkflowsPage } from '../pages/WorkflowsPage';
import History from '../pages/History';
import { ExecutionStudioPage } from '../pages/ExecutionStudioPage';
import { SettingsPage } from '../pages/SettingsPage';
import { ConnectorsPage } from '../pages/ConnectorsPage';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { TemplatesPage } from '../pages/TemplatesPage';
import { MarketplacePage } from '../pages/MarketplacePage';
import { ErrorReplayPage } from '../pages/ErrorReplayPage';
import { OAuthResultPage } from '../pages/OAuthResultPage';
import { ProtectedRoute } from './ProtectedRoute';
import { ErrorBoundary } from '../components/common/ErrorBoundary';

if (typeof window !== 'undefined') {
  const origPushState = history.pushState;
  const origReplaceState = history.replaceState;

  history.pushState = function (...args) {
    console.log('[AI30 NAVIGATION ATTEMPT]', {
      from: window.location.href,
      to: args[2],
      timestamp: Date.now(),
    });
    console.trace('[AI30 NAVIGATION CALLSTACK]');
    return origPushState.apply(this, args);
  };

  history.replaceState = function (...args) {
    console.log('[AI30 NAVIGATION ATTEMPT]', {
      from: window.location.href,
      to: args[2],
      timestamp: Date.now(),
    });
    console.trace('[AI30 NAVIGATION CALLSTACK]');
    return origReplaceState.apply(this, args);
  };

  window.addEventListener('popstate', () => {
    console.log('[AI30 NAVIGATION ATTEMPT] popstate event fired. Location:', window.location.href);
    console.trace('[AI30 NAVIGATION CALLSTACK]');
  });

  document.addEventListener(
    'click',
    (e) => {
      const target = e.target as HTMLElement;
      const anchor = target?.closest ? target.closest('a') : null;
      const button = target?.closest ? target.closest('button') : null;
      const form = target?.closest ? target.closest('form') : null;

      console.log('[AI30 CLICK]', {
        tag: target?.tagName,
        text: target?.textContent?.trim().substring(0, 40),
        href: (anchor as HTMLAnchorElement)?.href || (target as any)?.href,
        type: (button as HTMLButtonElement)?.type || (target as any)?.type,
        defaultPrevented: e.defaultPrevented,
        target: target,
        closestAnchorHref: anchor?.getAttribute('href'),
        closestFormAction: form?.getAttribute('action'),
      });
      console.trace('[AI30 CLICK CALLSTACK]');
    },
    true
  );

  window.addEventListener('beforeunload', () => {
    console.log('[AI30 BEFOREUNLOAD] BEFOREUNLOAD FIRED! Location:', window.location.href, 'activeElement:', document.activeElement?.tagName, document.activeElement);
    console.trace('[AI30 BEFOREUNLOAD CALLSTACK]');
  });
}

const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/signup', element: <SignupPage /> },
  { path: '/register', element: <RegisterPage /> },
  { path: '/oauth/result', element: <OAuthResultPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      { path: '/dashboard', element: <DashboardPage /> },
      { path: '/workflows', element: <WorkflowsPage /> },
      { path: '/builder', element: <WorkflowBuilderPage /> },
      { path: '/templates', element: <TemplatesPage /> },
      { path: '/discovery', element: <Navigate to="/templates" replace /> },
      { path: '/marketplace', element: <MarketplacePage /> },
      { path: '/connectors', element: <ConnectorsPage /> },
      { path: '/engine', element: <ExecutionStudioPage /> },
      { path: '/error-replay', element: <ErrorReplayPage /> },
      { path: '/history', element: <History /> },
      { path: '/profile', element: <Navigate to="/settings" replace /> },
      { path: '/activity', element: <AnalyticsPage /> },
      { path: '/analytics', element: <AnalyticsPage /> },
      { path: '/settings', element: <SettingsPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);

export function AppRouter() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
