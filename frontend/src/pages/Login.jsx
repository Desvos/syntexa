import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Stack, Typography } from '@mui/material';
import HubIcon from '@mui/icons-material/Hub';
import LoginForm from '../components/LoginForm.jsx';
import { isAuthenticated, setSessionExpiryHandler } from '../api/auth.js';

export default function LoginPage() {
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated()) {
      navigate('/', { replace: true });
      return;
    }
    setSessionExpiryHandler(() => {
      navigate('/login', { replace: true });
    });
  }, [navigate]);

  const handleLoginSuccess = () => {
    navigate('/', { replace: true });
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        px: 2,
        py: 6,
        position: 'relative',
        overflow: 'hidden',
        background: (t) =>
          t.palette.mode === 'dark'
            ? `radial-gradient(circle at 20% 10%, ${t.palette.primary.dark}55 0%, transparent 45%),
               radial-gradient(circle at 80% 90%, ${t.palette.secondary.dark}40 0%, transparent 45%),
               linear-gradient(180deg, #0b1220 0%, #111827 100%)`
            : `radial-gradient(circle at 20% 10%, ${t.palette.primary.light}40 0%, transparent 45%),
               radial-gradient(circle at 80% 90%, ${t.palette.secondary.light}35 0%, transparent 45%),
               linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)`,
      }}
    >
      <Stack spacing={4} alignItems="center" sx={{ width: '100%', maxWidth: 420 }}>
        <Stack direction="row" spacing={1.5} alignItems="center">
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: 2.5,
              display: 'grid',
              placeItems: 'center',
              background: (t) =>
                `linear-gradient(135deg, ${t.palette.primary.main} 0%, ${t.palette.secondary.main} 100%)`,
              color: 'common.white',
              boxShadow: (t) => `0 10px 30px ${t.palette.primary.main}55`,
            }}
          >
            <HubIcon />
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 700, lineHeight: 1 }}>
              Syntexa
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Agent Swarm Platform
            </Typography>
          </Box>
        </Stack>

        <LoginForm onSuccess={handleLoginSuccess} />
      </Stack>
    </Box>
  );
}
