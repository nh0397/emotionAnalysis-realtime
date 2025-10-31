import React, { useState } from 'react';
import html2canvas from 'html2canvas';
import './FloatingChatbot.css';

// Simple markdown parser for bot responses
function parseMarkdown(text) {
  if (!text) return text;
  
  // Convert **bold** to <strong>
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Convert bullet points (• text) to proper list items
  const lines = text.split('\n');
  let inList = false;
  let result = [];
  
  for (let line of lines) {
    const trimmed = line.trim();
    
    if (trimmed.startsWith('•')) {
      if (!inList) {
        result.push('<ul>');
        inList = true;
      }
      const listItem = trimmed.substring(1).trim();
      result.push(`<li>${listItem}</li>`);
    } else {
      if (inList) {
        result.push('</ul>');
        inList = false;
      }
      if (trimmed) {
        result.push(`<p>${trimmed}</p>`);
      }
    }
  }
  
  if (inList) {
    result.push('</ul>');
  }
  
  return result.join('');
}

export default function FloatingChatbot({ currentPage = 'live' }) {
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const [sqlModal, setSqlModal] = useState(null); // Track which SQL modal is open

  const captureScreenshot = async () => {
    setCapturing(true);
    try {
      const canvas = await html2canvas(document.body, {
        allowTaint: true,
        useCORS: true,
        logging: false,
        scale: 0.5
      });
      const base64 = canvas.toDataURL('image/png');
      setCapturing(false);
      return base64;
    } catch (err) {
      console.error('Screenshot failed:', err);
      setCapturing(false);
      return null;
    }
  };

  const ask = async () => {
    if (!question.trim()) return;

    setLoading(true);
    const userMessage = { 
      type: 'question', 
      text: question
    };
    // Add user message and immediate status notice so the user isn't kept waiting
    const statusMessage = {
      type: 'status',
      text: 'Working on your query — this may take a moment. If the engine is busy, we\'ll fall back automatically.'
    };
    setHistory(prev => [...prev, userMessage, statusMessage]);

    // Setup AbortController (no timeout - system is slow)
    let controller;

    try {
      controller = new AbortController();

      // Get or create session ID
      let sessionId = localStorage.getItem('chatSessionId');
      if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('chatSessionId', sessionId);
      }

      const endpoint = '/chat';
      const payload = {
        question: question.trim(),
        session_id: sessionId,
        current_page: currentPage  // Use the actual page state from Navigation
      };

      const response = await fetch(`http://localhost:9000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const botMessage = {
        type: 'answer',
        sql: data.sql,
        rows: data.rows || [],
        chartHint: data.chart_hint,
        message: data.message
      };

      // Replace the status notice with the final answer
      setHistory(prev => {
        const filtered = prev.filter(m => m.type !== 'status');
        return [...filtered, botMessage];
      });
      setQuestion('');
    } catch (err) {
      const message = err.message || 'Something went wrong. Please try again.';
      // Replace the status notice with a friendly error
      setHistory(prev => {
        const filtered = prev.filter(m => m.type !== 'status');
        return [...filtered, { type: 'error', text: 'The query engine is busy right now. Please try again in a moment.' }];
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      ask();
    }
  };

  const clearHistory = () => {
    setHistory([]);
    setSqlModal(null);
  };

  const openSqlModal = (messageData, messageIndex) => {
    setSqlModal({ ...messageData, index: messageIndex });
  };

  const closeSqlModal = () => {
    setSqlModal(null);
  };

  return (
    <>
      {/* Floating Button */}
      <div 
        className={`chatbot-fab ${isOpen ? 'hidden' : ''}`}
        onClick={() => setIsOpen(true)}
        title="Ask TecViz AI"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 2C6.48 2 2 6.48 2 12C2 13.93 2.6 15.72 3.6 17.2L2.05 21.95L6.8 20.4C8.28 21.4 10.07 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C10.33 20 8.77 19.48 7.47 18.6L7.1 18.35L4.55 19.05L5.25 16.55L4.97 16.15C4.06 14.83 3.5 13.23 3.5 11.5C3.5 7.36 6.86 4 11 4C15.14 4 18.5 7.36 18.5 11.5C18.5 15.64 15.14 19 11 19H12V20Z" fill="white"/>
          <circle cx="8" cy="12" r="1" fill="white"/>
          <circle cx="12" cy="12" r="1" fill="white"/>
          <circle cx="16" cy="12" r="1" fill="white"/>
        </svg>
      </div>

      {/* Chatbot Panel */}
      {isOpen && (
        <div className="chatbot-floating-panel">
          {/* Header */}
          <div className="chatbot-floating-header">
            <div className="chatbot-header-content">
              <h3>TecViz AI Assistant</h3>
              <span className="chatbot-subtitle">Ask about your data or UI</span>
            </div>
            <div className="chatbot-header-actions">
              {history.length > 0 && (
                <button 
                  className="chatbot-icon-btn" 
                  onClick={clearHistory}
                  title="Clear history"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14z" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </button>
              )}
              <button 
                className="chatbot-icon-btn" 
                onClick={() => setIsOpen(false)}
                title="Close"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M18 6L6 18M6 6l12 12" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </button>
            </div>
          </div>

          {/* Chat History */}
          <div className="chatbot-floating-history">
            {history.length === 0 && (
              <div className="chatbot-welcome">
                <div className="welcome-icon">💬</div>
                <h4>How can I help you?</h4>
                <p>Ask questions about your emotion data or the UI:</p>
                <div className="example-queries">
                  <button className="example-query" onClick={() => setQuestion("Show daily average anger in CA for last 30 days")}>
                    📊 Show daily anger in CA
                  </button>
                  <button className="example-query" onClick={() => setQuestion("What does this visualization show?")}>
                    🎨 Explain this view
                  </button>
                  <button className="example-query" onClick={() => setQuestion("Which state has highest joy?")}>
                    😊 Highest joy state
                  </button>
                </div>
              </div>
            )}

            {history.map((item, idx) => (
              <div key={idx} className={`chat-message chat-${item.type}`}>
                {item.type === 'question' && (
                  <div className="message-wrapper user-wrapper">
                    <div className="message-icon user-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <div className="message-bubble user-bubble">
                      <div className="bubble-content">
                        {item.text}
                      </div>
                    </div>
                  </div>
                )}

                {item.type === 'answer' && (
                  <div className="message-wrapper bot-wrapper">
                    <div className="message-icon bot-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <rect x="3" y="11" width="18" height="10" rx="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <circle cx="12" cy="5" r="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="m12 7-3 5h6l-3-5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <line x1="9" y1="9" x2="9.01" y2="9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <line x1="15" y1="9" x2="15.01" y2="9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <div className="message-bubble bot-bubble">
                      <div className="bubble-content">
                        {/* Natural Language Response - Always Visible */}
                        {item.message && (
                          <div 
                            className="nl-response bot-text"
                            dangerouslySetInnerHTML={{ __html: parseMarkdown(item.message) }}
                          />
                        )}

                        {/* Data Query Button - Show compact button if SQL/data exists */}
                        {(item.sql || (item.rows && item.rows.length > 0)) && (
                          <div className="data-action-section">
                            <button 
                              className="data-action-btn"
                              onClick={() => openSqlModal(item, idx)}
                              title="View query details and data"
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                                <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                                <path d="M9 9h6v6H9z" fill="currentColor"/>
                                <path d="M16 3v4M8 3v4M3 11h18" stroke="currentColor" strokeWidth="2"/>
                              </svg>
                              <span>Query Details</span>
                              {item.rows && item.rows.length > 0 && (
                                <span className="row-count">({item.rows.length} rows)</span>
                              )}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {(item.type === 'error' || item.type === 'status') && (
                  <div className="message-wrapper bot-wrapper">
                    <div className="message-icon bot-icon error-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                        <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" strokeWidth="2"/>
                        <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" strokeWidth="2"/>
                      </svg>
                    </div>
                    <div className="message-bubble error-bubble">
                      <div className="bubble-content">{item.text}</div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="chat-message chat-loading">
                <div className="message-wrapper bot-wrapper">
                  <div className="message-icon bot-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <rect x="3" y="11" width="18" height="10" rx="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <circle cx="12" cy="5" r="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="m12 7-3 5h6l-3-5z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <line x1="9" y1="9" x2="9.01" y2="9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      <line x1="15" y1="9" x2="15.01" y2="9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="message-bubble bot-bubble">
                    <div className="bubble-content">
                      <div className="typing-indicator">
                        <span></span><span></span><span></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Footer */}
          <div className="chatbot-floating-footer">
            <div className="input-row">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask anything..."
                disabled={loading}
                rows={1}
              />
              <button 
                onClick={ask}
                disabled={loading || !question.trim()}
                className="send-btn"
              >
                {loading ? '...' : '→'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SQL Data Modal */}
      {sqlModal && (
        <div className="sql-modal-overlay" onClick={closeSqlModal}>
          <div className="sql-modal" onClick={(e) => e.stopPropagation()}>
            <div className="sql-modal-header">
              <div className="modal-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
                  <path d="M9 9h6v6H9z" fill="currentColor"/>
                  <path d="M16 3v4M8 3v4M3 11h18" stroke="currentColor" strokeWidth="2"/>
                </svg>
                <span>Query Details</span>
              </div>
              <button className="modal-close-btn" onClick={closeSqlModal}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </button>
            </div>

            <div className="sql-modal-content">
              {sqlModal.sql && (
                <div className="modal-section">
                  <h4>SQL Query</h4>
                  <div className="sql-preview-modal">
                    <code>{sqlModal.sql}</code>
                  </div>
                </div>
              )}

              {sqlModal.rows && sqlModal.rows.length > 0 && (
                <div className="modal-section">
                  <h4>Results ({sqlModal.rows.length} rows)</h4>
                  <div className="results-table-modal">
                    <table className="results-table">
                      <thead>
                        <tr>
                          {Object.keys(sqlModal.rows[0]).map((col, i) => (
                            <th key={i}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {sqlModal.rows.map((row, i) => (
                          <tr key={i}>
                            {Object.values(row).map((val, j) => (
                              <td key={j}>{
                                typeof val === 'number' ? val.toFixed(3) :
                                typeof val === 'object' ? JSON.stringify(val) :
                                val
                              }</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {sqlModal.chartHint && (
                <div className="modal-section">
                  <div className="hint-badge-modal">
                    <strong>Visualization Suggestion:</strong> {sqlModal.chartHint}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

