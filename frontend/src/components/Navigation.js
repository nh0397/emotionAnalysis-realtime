import React from 'react';
import './Navigation.css';

function Navigation({ currentPage, onPageChange }) {
  const pages = [
    { id: 'live', name: 'Live Stream', description: 'Real-time tweets' },
    { id: 'history', name: 'History', description: 'All tweets from database' },
    { id: 'metrics', name: 'Analytics', description: 'System metrics' },
    { id: 'visualization', name: 'Emotion Map', description: 'Interactive D3.js visualizations' }
  ];

  return (
    <nav className="navigation">
      <div className="header-container">
        <div className="nav-header">
          <h1 className="app-title">TecVis 2.0</h1>
          <p className="app-subtitle">The Real Time Analytics Platform</p>
        </div>
        
        <div className="nav-tabs">
          {pages.map(page => (
            <button
              key={page.id}
              className={`nav-tab ${currentPage === page.id ? 'active' : ''}`}
              onClick={() => onPageChange(page.id)}
            >
              {page.name}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
