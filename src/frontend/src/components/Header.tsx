import React from 'react';
import './Header.css';

interface HeaderProps {
  currentPage: 'assets';
  onPageChange: (page: 'assets') => void;
}

const Header: React.FC<HeaderProps> = ({ currentPage, onPageChange }) => {
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
      </div>
    </header>
  );
};

export default Header; 