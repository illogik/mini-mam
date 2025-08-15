import React, { useState } from 'react';
import './App.css';
import AssetsPage from './components/AssetsPage';
import Header from './components/Header';
import LoginPage from './components/LoginPage';
import { AuthProvider, useAuth } from './contexts/AuthContext';

type Page = 'assets';

function AppContent() {
  const [currentPage, setCurrentPage] = useState<Page>('assets');
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="App">
      <Header currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="main-content">
        {currentPage === 'assets' && <AssetsPage />}
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
