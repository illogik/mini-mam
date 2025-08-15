import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './LoginPage.css';

const LoginPage: React.FC = () => {
  const { login, error, clearError, loading } = useAuth();
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
  });
  const [formErrors, setFormErrors] = useState({
    username: '',
    password: '',
  });

  // Clear error when component mounts
  useEffect(() => {
    clearError();
  }, [clearError]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear field error when user starts typing
    if (formErrors[name as keyof typeof formErrors]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = (): boolean => {
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
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await login(credentials);
    } catch (error) {
      // Error is handled by the auth context
      console.error('Login failed:', error);
    }
  };



  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>Mini-MAM</h1>
          <p>Media Asset Management System</p>
        </div>

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

          <button
            type="submit"
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>


      </div>
    </div>
  );
};

export default LoginPage; 