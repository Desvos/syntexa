import React, { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';

import CompositionsPage from './pages/Compositions.jsx';
import LoginPage from './pages/Login.jsx';
import MonitorPage from './pages/Monitor.jsx';
import RolesPage from './pages/Roles.jsx';
import SettingsPage from './pages/Settings.jsx';
import UsersPage from './pages/Users.jsx';
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
              <Navigate to="/roles" replace />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/roles"
          element={
            <AuthenticatedShell>
              <RolesPage />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/compositions"
          element={
            <AuthenticatedShell>
              <CompositionsPage />
            </AuthenticatedShell>
          }
        />
        <Route
          path="/monitor"
          element={
            <AuthenticatedShell>
              <MonitorPage />
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
