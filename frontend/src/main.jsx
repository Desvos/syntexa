import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes, Link, useLocation } from 'react-router-dom';

import CompositionsPage from './pages/Compositions.jsx';
import LoginPage from './pages/Login.jsx';
import MonitorPage from './pages/Monitor.jsx';
import RolesPage from './pages/Roles.jsx';
import SettingsPage from './pages/Settings.jsx';
import UsersPage from './pages/Users.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import { isAuthenticated, authApi, setSessionExpiryHandler, clearSessionExpiryHandler } from './api/auth.js';
import { setAuthErrorHandler } from './api/client.js';
import './styles/base.css';

function Navigation() {
  const location = useLocation();
  const [authenticated, setAuthenticated] = useState(isAuthenticated());

  useEffect(() => {
    setAuthenticated(isAuthenticated());

    // Set up session expiry handler
    if (authenticated) {
      setSessionExpiryHandler(() => {
        setAuthenticated(false);
        window.location.href = '/login';
      });
    }

    // Set up 401 handler for API calls with invalid token
    setAuthErrorHandler(() => {
      setAuthenticated(false);
    });

    return () => {
      clearSessionExpiryHandler();
    };
  }, [authenticated]);

  const handleLogout = async () => {
    await authApi.logout();
    setAuthenticated(false);
  };

  // Don't show nav on login page
  if (location.pathname === '/login') {
    return null;
  }

  // Don't show nav if not authenticated
  if (!authenticated) {
    return null;
  }

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="main-nav">
      <div className="nav-brand">Syntexa</div>
      <ul className="nav-links">
        <li>
          <Link to="/roles" className={isActive('/roles') ? 'active' : ''}>
            Agent Roles
          </Link>
        </li>
        <li>
          <Link to="/compositions" className={isActive('/compositions') ? 'active' : ''}>
            Compositions
          </Link>
        </li>
        <li>
          <Link to="/monitor" className={isActive('/monitor') ? 'active' : ''}>
            Monitor
          </Link>
        </li>
        <li>
          <Link to="/users" className={isActive('/users') ? 'active' : ''}>
            Users
          </Link>
        </li>
        <li>
          <Link to="/settings" className={isActive('/settings') ? 'active' : ''}>
            Settings
          </Link>
        </li>
      </ul>
      <div className="nav-actions">
        <button className="btn btn-secondary" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Navigate to="/roles" replace />
                </ProtectedRoute>
              }
            />
            <Route
              path="/roles"
              element={
                <ProtectedRoute>
                  <RolesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/compositions"
              element={
                <ProtectedRoute>
                  <CompositionsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/monitor"
              element={
                <ProtectedRoute>
                  <MonitorPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
