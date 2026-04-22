import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  FormControl,
  IconButton,
  InputAdornment,
  InputLabel,
  OutlinedInput,
  TextField,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import { authApi } from '../api/auth.js';

/**
 * LoginForm - MUI-based login form component
 *
 * Features:
 * - Material Design form fields with validation
 * - Password visibility toggle
 * - Loading state with spinner
 * - Error display via Alert component
 * - Accessible labels and focus management
 */
export default function LoginForm({ onSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authApi.login(username, password);
      onSuccess();
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePassword = () => {
    setShowPassword((prev) => !prev);
  };

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  return (
    <Card
      sx={{
        width: '100%',
        backdropFilter: 'blur(10px)',
        backgroundColor: (t) =>
          t.palette.mode === 'dark'
            ? 'rgba(17, 24, 39, 0.85)'
            : 'rgba(255, 255, 255, 0.85)',
        boxShadow: (t) =>
          t.palette.mode === 'dark'
            ? '0 24px 48px rgba(0,0,0,0.5)'
            : '0 24px 48px rgba(99,102,241,0.18)',
      }}
    >
      <CardHeader
        title={
          <Typography variant="h5" component="h1" align="center" gutterBottom>
            Sign In
          </Typography>
        }
        subheader={
          <Typography variant="body2" color="text.secondary" align="center">
            Enter your credentials to access the dashboard
          </Typography>
        }
        sx={{ pb: 0 }}
      />

      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} role="alert">
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            autoFocus
            fullWidth
            required
            id="username"
            label="Username"
            name="username"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
            margin="normal"
            placeholder="Enter your username"
          />

          <FormControl fullWidth margin="normal" variant="outlined">
            <InputLabel htmlFor="password-input" required>
              Password
            </InputLabel>
            <OutlinedInput
              id="password-input"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              placeholder="Enter your password"
              required
              endAdornment={
                <InputAdornment position="end">
                  <IconButton
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    onClick={handleTogglePassword}
                    onMouseDown={handleMouseDownPassword}
                    edge="end"
                    size="small"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              }
              label="Password"
            />
          </FormControl>

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading || !username || !password}
            sx={{ mt: 3, mb: 2, py: 1.5 }}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              'Sign In'
            )}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}
