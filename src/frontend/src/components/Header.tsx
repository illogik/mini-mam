import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

interface HeaderProps {
  currentPage: 'assets';
  onPageChange: (page: 'assets') => void;
}

const Header: React.FC<HeaderProps> = ({ currentPage, onPageChange }) => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="logo">Mini-MAM</h1>
        <nav className="navigation">
          <button
            className={`nav-button ${currentPage === 'assets' ? 'active' : ''}`}
            onClick={() => onPageChange('assets')}
          >
            Assets
          </button>
        </nav>
        <div className="user-section">
          {user && (
            <div className="user-info">
              <span className="username">{user.username}</span>
              <span className="user-role">({user.role})</span>
            </div>
          )}
          <button className="logout-button" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header; 