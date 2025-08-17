import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './LoginPage.css';

const LoginPage: React.FC = React.memo(() => {
  const { login, error, clearError, loading } = useAuth();
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [formErrors, setFormErrors] = useState({
    username: '',
    password: '',
  });

  // Clear error when component mounts (but only if there's no existing error)
  useEffect(() => {
    // Only clear error on mount if there's no current error
    // This prevents clearing errors that should be displayed
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear field error when user starts typing
    setFormErrors(prev => {
      if (prev[name as keyof typeof prev]) {
        return {
          ...prev,
          [name]: ''
        };
      }
      return prev;
    });
    
    // Don't clear auth error immediately - let user see the error
    // Only clear when they start a new login attempt
  }, []);

  const validateForm = useCallback((): boolean => {
    const errors = {
      username: '',
      password: '',
    };

    if (!credentials.username.trim()) {
      errors.username = 'Username is required';
    }

    if (!credentials.password.trim()) {
      errors.password = 'Password is required';
    }

    setFormErrors(errors);
    return !errors.username && !errors.password;
  }, [credentials.username, credentials.password]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clear any previous error when starting a new login attempt
    if (error) {
      clearError();
    }
    
    if (!validateForm()) {
      return;
    }

    try {
      await login(credentials);
      // Success - user will be redirected automatically by auth context
    } catch (error) {
      // Error is handled by the auth context
      console.error('Login failed:', error);
    }
  }, [validateForm, login, credentials, error, clearError]);

  // Memoize the form JSX to prevent unnecessary re-renders
  const loginForm = useMemo(() => (
    <form className="login-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          type="text"
          id="username"
          name="username"
          value={credentials.username}
          onChange={handleInputChange}
          className={formErrors.username ? 'error' : ''}
          placeholder="Enter your username"
          disabled={loading}
        />
        {formErrors.username && (
          <span className="error-message">{formErrors.username}</span>
        )}
      </div>

      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          type="password"
          id="password"
          name="password"
          value={credentials.password}
          onChange={handleInputChange}
          className={formErrors.password ? 'error' : ''}
          placeholder="Enter your password"
          disabled={loading}
        />
        {formErrors.password && (
          <span className="error-message">{formErrors.password}</span>
        )}
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}
      
      {/* Debug info - remove in production */}
      {process.env.NODE_ENV === 'development' && error && (
        <div style={{ fontSize: '12px', color: '#666', marginTop: '10px' }}>
          Debug: Error state is active
        </div>
      )}

      <button
        type="submit"
        className="login-button"
        disabled={loading}
      >
        {loading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
  ), [handleSubmit, credentials, formErrors, handleInputChange, loading, error]);

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>Mini-MAM</h1>
          <p>Media Asset Management System</p>
        </div>

        {loginForm}
      </div>
    </div>
  );
});

export default LoginPage; 