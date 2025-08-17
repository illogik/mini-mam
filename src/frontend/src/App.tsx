import React, { useState, useCallback, useMemo } from 'react';
import './App.css';
import AssetsPage from './components/AssetsPage';
import Header from './components/Header';
import LoginPage from './components/LoginPage';
import LoadingSpinner from './components/LoadingSpinner';
import { AuthProvider, useAuth } from './contexts/AuthContext';

type Page = 'assets';

const AppContent: React.FC = React.memo(() => {
  const [currentPage, setCurrentPage] = useState<Page>('assets');
  const { isAuthenticated, loading } = useAuth();

  const handlePageChange = useCallback((page: Page) => {
    setCurrentPage(page);
  }, []);

  const loadingContent = useMemo(() => (
    <div className="loading-container">
      <LoadingSpinner />
      <p>Loading...</p>
    </div>
  ), []);

  const authenticatedContent = useMemo(() => (
    <div className="App">
      <Header currentPage={currentPage} onPageChange={handlePageChange} />
      <main className="main-content">
        {currentPage === 'assets' && <AssetsPage />}
      </main>
    </div>
  ), [currentPage, handlePageChange]);

  if (loading) {
    return loadingContent;
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return authenticatedContent;
});

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
