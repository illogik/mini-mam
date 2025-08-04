import React, { useState } from 'react';
import './App.css';
import AssetsPage from './components/AssetsPage';
import Header from './components/Header';

type Page = 'assets';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('assets');

  return (
    <div className="App">
      <Header currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="main-content">
        {currentPage === 'assets' && <AssetsPage />}
      </main>
    </div>
  );
}

export default App;
