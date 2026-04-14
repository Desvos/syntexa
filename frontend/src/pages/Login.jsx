import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/LoginForm.jsx';
import { isAuthenticated, setSessionExpiryHandler } from '../api/auth.js';

/**
 * Login page component.
 * Redirects to home if already authenticated.
 */
export default function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect if already logged in
    if (isAuthenticated()) {
      navigate('/', { replace: true });
      return;
    }

    // Set up session expiry handler
    setSessionExpiryHandler(() => {
      navigate('/login', { replace: true });
    });

    return () => {
      // Cleanup expiry handler on unmount
      // (keep it active for other components)
    };
  }, [navigate]);

  const handleLoginSuccess = () => {
    navigate('/', { replace: true });
  };

  return (
    <div className="login-page">
      <div className="login-page-header">
        <h1>Syntexa</h1>
        <p>Agent Swarm Platform</p>
      </div>
      <LoginForm onSuccess={handleLoginSuccess} />
    </div>
  );
}
