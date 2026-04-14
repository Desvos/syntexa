import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import CompositionsPage from './pages/Compositions.jsx';
import MonitorPage from './pages/Monitor.jsx';
import RolesPage from './pages/Roles.jsx';
import SettingsPage from './pages/Settings.jsx';
import './styles/base.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <nav className="main-nav">
          <div className="nav-brand">Syntexa</div>
          <ul className="nav-links">
            <li>
              <a href="/roles" className={window.location.pathname === '/roles' ? 'active' : ''}>
                Agent Roles
              </a>
            </li>
            <li>
              <a href="/compositions" className={window.location.pathname === '/compositions' ? 'active' : ''}>
                Compositions
              </a>
            </li>
            <li>
              <a href="/monitor" className={window.location.pathname === '/monitor' ? 'active' : ''}>
                Monitor
              </a>
            </li>
            <li>
              <a href="/settings" className={window.location.pathname === '/settings' ? 'active' : ''}>
                Settings
              </a>
            </li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/roles" replace />} />
            <Route path="/roles" element={<RolesPage />} />
            <Route path="/compositions" element={<CompositionsPage />} />
            <Route path="/monitor" element={<MonitorPage />} />
            <Route path="/settings" element={<SettingsPage />} />
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
