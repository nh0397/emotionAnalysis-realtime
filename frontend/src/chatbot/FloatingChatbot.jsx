import React, { useMemo, useState } from 'react';
import html2canvas from 'html2canvas';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, Cell, ComposedChart, Area, AreaChart
} from 'recharts';
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
  const [copied, setCopied] = useState(false);    // Copy-to-clipboard feedback
  const [showChartPreview, setShowChartPreview] = useState(false); // Render chart on demand only

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
    // Only add the user message; status messages will be added conditionally based on backend notice
    setHistory(prev => [...prev, userMessage]);

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

      const notice = data.notice;
      setHistory(prev => {
        const msgs = [...prev];
        if (notice === 'gemini_rate_limited' || notice === 'gemini_fallback') {
          msgs.push({ type: 'status', text: 'Gemini rate-limited. Falling back to local model.' });
        }
        msgs.push(botMessage);
        return msgs;
      });
      setQuestion('');
    } catch (err) {
      const message = err.message || 'Something went wrong. Please try again.';
      setHistory(prev => [...prev, { type: 'error', text: 'The query engine is busy right now. Please try again in a moment.' }]);
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
    setShowChartPreview(false);
    setCopied(false);
    setSqlModal({ ...messageData, index: messageIndex });
  };

  const closeSqlModal = () => {
    setSqlModal(null);
  };

  // Smart multi-dimensional chart renderer using Recharts
  const ChartRenderer = ({ rows, hint }) => {
    const chartData = useMemo(() => {
      if (!rows || rows.length === 0) return null;

      const cols = Object.keys(rows[0] || {});
      const numericCols = cols.filter(c => typeof rows[0][c] === 'number');
      const categoricalCols = cols.filter(c => typeof rows[0][c] !== 'number');
      const dateKey = cols.find(c => /date|timestamp/i.test(c));
      const stateKey = cols.find(c => /state_name|state_code/i.test(c));
      const emotionCols = ['anger', 'fear', 'sadness', 'joy', 'surprise', 'anticipation', 'trust', 'disgust']
        .filter(e => cols.some(c => c.toLowerCase().includes(e)));

      // Determine chart type from hint or data shape
      const chartType = hint || (() => {
        if (dateKey && numericCols.length === 1) return 'line_chart';
        if (dateKey && numericCols.length > 1) return 'multi_line_chart';
        // Multi-dimensional emotion data: use heatmap for many states/emotions, radar for fewer
        if (emotionCols.length >= 3 && stateKey) {
          if (rows.length >= 5 && emotionCols.length >= 5) return 'heatmap';
          if (rows.length <= 4 && emotionCols.length <= 6) return 'radar_chart';
          return 'heatmap'; // Default to heatmap for clarity
        }
        // General multi-dimensional data
        if (numericCols.length >= 3 && stateKey) {
          return rows.length <= 15 && numericCols.length <= 4 ? 'grouped_bar_chart' : 'heatmap';
        }
        if (stateKey && numericCols.length === 1) {
          return rows.length <= 10 ? 'horizontal_bar_chart' : 'bar_chart';
        }
        if (stateKey && numericCols.length === 2) return 'grouped_bar_chart';
        return 'bar_chart';
      })();

      return { chartType, rows, cols, numericCols, categoricalCols, dateKey, stateKey, emotionCols };
    }, [rows, hint]);

    if (!chartData || !chartData.rows) return null;

    const { chartType, rows: dataRows, numericCols, dateKey, stateKey, emotionCols } = chartData;

    // Radar Chart - Multi-dimensional emotion data per state
    // For radar charts, each row (state) has all emotions, and we show multiple states as overlays
    if (chartType === 'radar_chart' && emotionCols.length >= 3 && stateKey) {
      // Map emotion column names to actual column names
      const emotionMap = {};
      emotionCols.forEach(emotion => {
        const col = numericCols.find(c => c.toLowerCase().includes(emotion));
        if (col) emotionMap[emotion] = col;
      });

      // Prepare data: each state becomes a radar series
      const radarData = dataRows.slice(0, 5).map(row => {
        const data = { state: (row[stateKey] || 'Unknown').substring(0, 12) };
        Object.keys(emotionMap).forEach(emotion => {
          const col = emotionMap[emotion];
          data[emotion] = Number(row[col]) || 0;
        });
        return data;
      });

      const colors = ['#4ea1ff', '#ff6b6b', '#51cf66', '#ffd43b', '#845ef7'];
      
      return (
        <div style={{ width: '100%', height: '400px', padding: '10px 0' }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis 
                dataKey="state" 
                tick={{ fill: '#bbb', fontSize: 11 }}
              />
              <PolarRadiusAxis 
                angle={90} 
                domain={[0, 1]} 
                tick={{ fill: '#bbb', fontSize: 10 }}
              />
              {radarData.map((item, idx) => (
                <Radar
                  key={item.state}
                  name={item.state}
                  dataKey={item.state}
                  stroke={colors[idx % colors.length]}
                  fill={colors[idx % colors.length]}
                  fillOpacity={0.3}
                  dot={false}
                />
              ))}
              <Tooltip />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    // Heatmap - States x Emotions (for many states and emotions)
    if (chartType === 'heatmap' && stateKey && emotionCols.length >= 5) {
      const heatmapData = dataRows.slice(0, 10).map(row => {
        const state = row[stateKey] || 'Unknown';
        const data = { state };
        emotionCols.forEach(emotion => {
          const col = numericCols.find(c => c.toLowerCase().includes(emotion));
          if (col) data[emotion] = Number(row[col]) || 0;
        });
        return data;
      });

      return (
        <div style={{ width: '100%', height: '400px', padding: '10px 0' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={heatmapData} layout="vertical" margin={{ top: 20, right: 30, left: 80, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
              <XAxis type="number" domain={[0, 1]} tick={{ fill: '#bbb', fontSize: 11 }} />
              <YAxis 
                dataKey="state" 
                type="category" 
                width={70}
                tick={{ fill: '#bbb', fontSize: 10 }}
              />
              <Tooltip />
              <Legend />
              {emotionCols.slice(0, 8).map((emotion, idx) => {
                const colors = ['#4ea1ff', '#ff6b6b', '#51cf66', '#ffd43b', '#845ef7', '#ff8787', '#74c0fc', '#ffa94d'];
                return (
                  <Bar 
                    key={emotion} 
                    dataKey={emotion} 
                    stackId="a" 
                    fill={colors[idx % colors.length]}
                    opacity={0.8}
                  />
                );
              })}
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    // Grouped Bar Chart - States vs 2-4 metrics
    if (chartType === 'grouped_bar_chart' && stateKey && numericCols.length >= 2) {
      const groupedData = dataRows.slice(0, 10).map(row => {
        const data = { state: (row[stateKey] || 'Unknown').substring(0, 10) };
        numericCols.slice(0, 4).forEach(col => {
          data[col] = Number(row[col]) || 0;
        });
        return data;
      });

      const colors = ['#4ea1ff', '#ff6b6b', '#51cf66', '#ffd43b'];
      
      return (
        <div style={{ width: '100%', height: '350px', padding: '10px 0' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={groupedData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
              <XAxis 
                dataKey="state" 
                angle={-45} 
                textAnchor="end" 
                height={80}
                tick={{ fill: '#bbb', fontSize: 10 }}
              />
              <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
              <Tooltip />
              <Legend />
              {numericCols.slice(0, 4).map((col, idx) => (
                <Bar 
                  key={col} 
                  dataKey={col} 
                  fill={colors[idx % colors.length]}
                  opacity={0.8}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    // Line Chart - Time series
    if (chartType === 'line_chart' && dateKey && numericCols.length >= 1) {
      const sorted = [...dataRows].sort((a, b) => {
        const d1 = new Date(a[dateKey]);
        const d2 = new Date(b[dateKey]);
        return d1 - d2;
      });
      const metric = numericCols[0];

      return (
        <div style={{ width: '100%', height: '350px', padding: '10px 0' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sorted} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4ea1ff" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#4ea1ff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
              <XAxis 
                dataKey={dateKey} 
                tick={{ fill: '#bbb', fontSize: 10 }}
                tickFormatter={(v) => new Date(v).toLocaleDateString()}
              />
              <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
              <Tooltip 
                labelFormatter={(v) => new Date(v).toLocaleDateString()}
                formatter={(v) => Number(v).toFixed(3)}
              />
              <Area 
                type="monotone" 
                dataKey={metric} 
                stroke="#4ea1ff" 
                fillOpacity={1} 
                fill="url(#colorArea)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      );
    }

    // Horizontal Bar Chart - Top N rankings
    if (chartType === 'horizontal_bar_chart' && stateKey && numericCols.length === 1) {
      const sorted = [...dataRows].sort((a, b) => (b[numericCols[0]] || 0) - (a[numericCols[0]] || 0));
      const barData = sorted.slice(0, 10).map(row => ({
        state: (row[stateKey] || 'Unknown').substring(0, 15),
        value: Number(row[numericCols[0]]) || 0
      }));

      return (
        <div style={{ width: '100%', height: '350px', padding: '10px 0' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} layout="vertical" margin={{ top: 5, right: 30, left: 80, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
              <XAxis type="number" tick={{ fill: '#bbb', fontSize: 11 }} />
              <YAxis 
                dataKey="state" 
                type="category" 
                width={70}
                tick={{ fill: '#bbb', fontSize: 10 }}
              />
              <Tooltip formatter={(v) => Number(v).toFixed(3)} />
              <Bar dataKey="value" fill="#4ea1ff" opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    // Default: Simple Bar Chart
    if (stateKey && numericCols.length === 1) {
      const barData = dataRows.slice(0, 15).map(row => ({
        state: (row[stateKey] || 'Unknown').substring(0, 12),
        value: Number(row[numericCols[0]]) || 0
      }));

      return (
        <div style={{ width: '100%', height: '350px', padding: '10px 0' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
              <XAxis 
                dataKey="state" 
                angle={-45} 
                textAnchor="end" 
                height={80}
                tick={{ fill: '#bbb', fontSize: 10 }}
              />
              <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
              <Tooltip formatter={(v) => Number(v).toFixed(3)} />
              <Bar dataKey="value" fill="#4ea1ff" opacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    return null;
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
          <div className="sql-modal" onClick={(e) => e.stopPropagation()} style={{ width: '820px', maxWidth: '94vw', maxHeight: '80vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
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

            <div className="sql-modal-content" style={{ overflow: 'auto' }}>
              {sqlModal.sql && (
                <div className="modal-section">
                  <h4>SQL Query</h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <button
                      className="data-action-btn"
                      onClick={() => {
                        try {
                          navigator.clipboard.writeText(sqlModal.sql);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 1500);
                        } catch (e) {
                          console.error('Copy failed', e);
                        }
                      }}
                      title="Copy SQL to clipboard"
                    >
                      Copy SQL
                    </button>
                    {copied && (
                      <span style={{ color: '#7CFC00', fontSize: '12px' }}>Copied!</span>
                    )}
                  </div>
                  <div className="sql-preview-modal">
                    <code>{sqlModal.sql}</code>
                  </div>
                </div>
              )}

              {sqlModal.rows && sqlModal.rows.length > 0 && (
                <div className="modal-section" style={{ maxHeight: '48vh', overflow: 'auto' }}>
                  <h4>Results ({sqlModal.rows.length} rows)</h4>
                  <div className="results-table-modal" style={{ overflow: 'auto' }}>
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

              {(sqlModal.chartHint || (sqlModal.rows && sqlModal.rows.length > 0)) && (
                <div className="modal-section">
                  <div className="hint-badge-modal">
                    <strong>Visualization Suggestion:</strong> {sqlModal.chartHint || 'Auto-detected'}
                  </div>
                  {/* Render on demand to avoid overhead */}
                  <div style={{ marginTop: '10px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <button
                      className="data-action-btn"
                      onClick={() => setShowChartPreview(prev => !prev)}
                      title={showChartPreview ? 'Hide visualization' : 'Visualize results'}
                    >
                      {showChartPreview ? 'Hide Visualization' : 'Visualize'}
                    </button>
                  </div>
                  {showChartPreview && (
                    <div style={{ marginTop: '10px' }}>
                      <ChartRenderer rows={sqlModal.rows} hint={sqlModal.chartHint} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

