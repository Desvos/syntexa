import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom';

import LoginPage from './pages/Login.jsx';
import SettingsPage from './pages/Settings.jsx';
import UsersPage from './pages/Users.jsx';
import WizardPage from './pages/Wizard.jsx';
import LLMProvidersPage from './pages/LLMProviders.jsx';
import AgentsPage from './pages/Agents.jsx';
import RepositoriesPage from './pages/Repositories.jsx';
import SwarmsPage from './pages/Swarms.jsx';
import AppLayout from './components/AppLayout.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import { ThemeContextProvider } from './components/ThemeContextProvider.jsx';
import { setSessionExpiryHandler, clearSessionExpiryHandler } from './api/auth.js';
import { setAuthErrorHandler } from './api/client.js';
import './styles/base.css';

function AuthenticatedShell({ children }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

function AuthBootstrap() {
  const location = useLocation();

  useEffect(() => {
    setSessionExpiryHandler(() => {
      window.location.href = '/login';
    });
    setAuthErrorHandler(() => {
      if (location.pathname !== '/login') {
        window.location.href = '/login';
      }
    });
    return () => {
      clearSessionExpiryHandler();
    };
  }, [location.pathname]);

  return null;
}

function App() {
  return (
    <BrowserRouter>
      <AuthBootstrap />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <AuthenticatedShell>
              <WizardPage />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/llm-providers"
          element={
            <AuthenticatedShell>
              <LLMProvidersPage />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/agents"
          element={
            <AuthenticatedShell>
              <AgentsPage />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/repositories"
          element={
            <AuthenticatedShell>
              <RepositoriesPage />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/swarms"
          element={
            <AuthenticatedShell>
              <SwarmsPage />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/users"
          element={
            <AuthenticatedShell>
              <UsersPage />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/settings"
          element={
            <AuthenticatedShell>
              <SettingsPage />
            </AuthenticatedShell>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeContextProvider>
      <App />
    </ThemeContextProvider>
  </React.StrictMode>
);
