import React, { useMemo, useState } from 'react';
import html2canvas from 'html2canvas';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, Cell, ComposedChart, Area, AreaChart
} from 'recharts';
import { Brain, User, TrendingUp, X, Trash2 } from 'lucide-react';
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
  const [showChartPreview, setShowChartPreview] = useState(true); // Render chart on demand - OPEN BY DEFAULT
  const [showDataTable, setShowDataTable] = useState(true); // Collapsible data table - OPEN BY DEFAULT
  const [showSqlQuery, setShowSqlQuery] = useState(true); // Collapsible SQL query - OPEN BY DEFAULT
  const [showVisualization, setShowVisualization] = useState(true); // Collapsible visualization - OPEN BY DEFAULT

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
        chartConfig: data.chart_config, // New: Rich config
        chartReasoning: data.chart_reasoning, // New: Reasoning
        chartCode: data.chart_code, // New: Generated Code
        message: data.message,
        autoShowViz: data.auto_show_viz || false
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
      
      // Microsoft Fabric-inspired: Auto-open modal and show visualization if appropriate
      if (botMessage.autoShowViz && (botMessage.sql || (botMessage.rows && botMessage.rows.length > 0))) {
        setTimeout(() => {
          const messageIndex = history.length + (notice ? 1 : 0);
          openSqlModal(botMessage, messageIndex);
          // Auto-expand visualization section (Microsoft Fabric style)
          setShowVisualization(true);
          setShowChartPreview(true);
          // Auto-expand SQL query too for transparency
          setShowSqlQuery(true);
        }, 400); // Small delay for smooth UX animation
      }
      
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
    setShowDataTable(false); // Reset table state when modal closes
    setShowChartPreview(false); // Reset chart state when modal closes
    setShowSqlQuery(false); // Reset SQL query state when modal closes
    setShowVisualization(false); // Reset visualization state when modal closes (also resets chart preview)
  };

  // Smart multi-dimensional chart renderer using Recharts
  const ChartRenderer = ({ rows, hint, config, code }) => {
    // Calculate chart data first
    const chartData = useMemo(() => {
      console.log('[ChartRenderer] Starting chartData calculation');
      
      if (!rows || rows.length === 0) {
        return null;
      }

      const cols = Object.keys(rows[0] || {});
      const numericCols = cols.filter(c => typeof rows[0][c] === 'number');
      const categoricalCols = cols.filter(c => typeof rows[0][c] !== 'number');
      const dateKey = cols.find(c => /date|timestamp/i.test(c));
      const stateKey = cols.find(c => /state_name|state_code/i.test(c));
      
      // Improved emotion detection
      const emotionCols = ['anger', 'fear', 'sadness', 'joy', 'surprise', 'anticipation', 'trust', 'disgust']
        .filter(e => cols.some(c => c.toLowerCase().includes(e)));
      
      // Generic numeric columns handling
      const hasGenericNumericCols = numericCols.some(c => /^avg(_\d+)?$/i.test(c));
      const hasMultipleNumericWithState = numericCols.length >= 3 && stateKey && hasGenericNumericCols;
      
      let emotionToColumnMap = {};
      if (hasMultipleNumericWithState && emotionCols.length === 0) {
        const emotionNames = ['anger', 'fear', 'sadness', 'joy', 'surprise', 'anticipation', 'trust', 'disgust'];
        emotionCols.push(...emotionNames.slice(0, numericCols.length));
        numericCols.forEach((col, idx) => {
          if (idx < emotionNames.length) {
            emotionToColumnMap[emotionNames[idx]] = col;
          }
        });
      } else {
        emotionCols.forEach(emotion => {
          const col = numericCols.find(c => c.toLowerCase().includes(emotion));
          if (col) emotionToColumnMap[emotion] = col;
        });
      }

      // Determine chart type
      const chartType = hint || (() => {
        // Fallback logic
        if (stateKey && numericCols.length >= 2) return 'grouped_bar_chart';
        if (dateKey && numericCols.length >= 1) return 'line_chart';
        return 'bar_chart';
      })();

      return { chartType, rows, cols, numericCols, categoricalCols, dateKey, stateKey, emotionCols, emotionToColumnMap };
    }, [rows, hint]);

    // Extract data for hooks
    const emotionCols = chartData?.emotionCols || [];
    const stateKey = chartData?.stateKey || null;
    const dataRows = chartData?.rows || [];
    
    // Filter state management
    const [selectedEmotions, setSelectedEmotions] = useState(() => {
      if (emotionCols.length > 0) return emotionCols;
      return [];
    });
    const [selectedStates, setSelectedStates] = useState(() => {
      if (stateKey && dataRows.length > 0) {
        return [...new Set(dataRows.map(r => r[stateKey]).filter(Boolean))];
      }
      return [];
    });
    
    // AI Enhancement State
    const [enhancing, setEnhancing] = useState(false);
    const [smartHint, setSmartHint] = useState(null);
    const [smartConfig, setSmartConfig] = useState(null);
    const [smartReasoning, setSmartReasoning] = useState(null);
    
    // Apply filters
    const filteredRows = useMemo(() => {
      if (!dataRows || dataRows.length === 0) return [];
      let filtered = dataRows;
      if (selectedStates.length > 0 && stateKey) {
        filtered = filtered.filter(row => selectedStates.includes(row[stateKey]));
      }
      return filtered;
    }, [dataRows, selectedStates, stateKey]);

    if (!chartData || !chartData.rows) return null;

    // Use smart hint if available, otherwise original hint or fallback
    const { chartType: baseChartType, numericCols, dateKey, emotionToColumnMap, cols } = chartData;
    const effectiveChartType = smartHint || baseChartType;
    
    // Use config if available to override defaults (e.g. colors)
    const activeConfig = smartConfig || config;
    const colors = activeConfig?.colors || ['#4ea1ff', '#ff6b6b', '#51cf66', '#ffd43b', '#845ef7', '#ff8787', '#74c0fc', '#ffa94d'];

    // Determine fallback chain based on data structure
    const getFallbackChartTypes = (primaryType) => {
      // Smart fallback: If we have sentiment/count columns, prioritize stacked_bar_chart
      const hasCompositionColumns = cols.some(c => /sentiment_|_count|_percentage|breakdown/i.test(c));
      
      const fallbacks = {
        'radar_chart': hasCompositionColumns 
          ? ['stacked_bar_chart', 'grouped_bar_chart', 'heatmap', 'bar_chart']
          : ['heatmap', 'grouped_bar_chart', 'stacked_bar_chart', 'bar_chart'],
        'heatmap': hasCompositionColumns
          ? ['stacked_bar_chart', 'grouped_bar_chart', 'bar_chart']
          : ['grouped_bar_chart', 'stacked_bar_chart', 'bar_chart'],
        'grouped_bar_chart': hasCompositionColumns
          ? ['stacked_bar_chart', 'bar_chart', 'horizontal_bar_chart']
          : ['stacked_bar_chart', 'bar_chart', 'horizontal_bar_chart'],
        'stacked_bar_chart': ['grouped_bar_chart', 'bar_chart'],
        'bar_chart': ['horizontal_bar_chart', 'grouped_bar_chart'],
        'horizontal_bar_chart': ['bar_chart'],
        'multi_line_chart': ['line_chart', 'bar_chart'],
        'line_chart': ['area_chart', 'bar_chart']
      };
      return fallbacks[primaryType] || (hasCompositionColumns ? ['stacked_bar_chart', 'bar_chart'] : ['bar_chart', 'horizontal_bar_chart']);
    };
    
    // Try chart types in order: primary -> fallbacks
    const chartTypesToTry = [effectiveChartType, ...getFallbackChartTypes(effectiveChartType)];
    
    // Function to trigger AI enhancement
    const enhanceWithAI = async () => {
      if (enhancing) return;
      setEnhancing(true);
      try {
        const response = await fetch('http://localhost:9000/chat/smart_suggest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sql: history[history.length-1]?.sql, // Last SQL
            rows: rows,
            question: history.length > 1 ? history[history.length-2].text : '' // Last question
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.chart_hint) {
            setSmartHint(data.chart_hint);
            setSmartConfig(data.chart_config);
            setSmartReasoning(data.chart_reasoning);
          }
        }
      } catch (e) {
        console.error("AI enhancement failed", e);
      } finally {
        setEnhancing(false);
      }
    };
    
    // Filter UI component
    const FilterControls = () => {
      return (
        <div style={{ 
          marginBottom: '16px', 
          padding: '12px', 
          background: '#1a1a1a', 
          borderRadius: '6px',
          border: '1px solid #333'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: '#fff' }}>
              Filters & Controls
            </div>
            
            <button 
              onClick={enhanceWithAI}
              disabled={enhancing || smartHint}
              style={{
                background: smartHint ? '#2a2a2a' : 'linear-gradient(45deg, #4ea1ff, #845ef7)',
                border: 'none',
                borderRadius: '4px',
                color: smartHint ? '#888' : '#fff',
                padding: '4px 8px',
                fontSize: '11px',
                cursor: smartHint ? 'default' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontWeight: '500'
              }}
            >
              {enhancing ? (
                <>
                  <div className="spinner-small" style={{width: 10, height: 10, border: '2px solid rgba(255,255,255,0.3)', borderTop: '2px solid #fff', borderRadius: '50%', animation: 'spin 1s linear infinite'}}></div>
                  Analyzing...
                </>
              ) : smartHint ? (
                <>✨ Reinforced by AI</>
              ) : (
                <>✨ Enhance with AI</>
              )}
            </button>
          </div>
          
          {smartReasoning && (
             <div style={{ fontSize: '11px', color: '#4ea1ff', background: 'rgba(78, 161, 255, 0.1)', padding: '6px', borderRadius: '4px', marginBottom: '8px' }}>
               <strong>AI Reasoning:</strong> {smartReasoning}
             </div>
          )}

          {emotionCols.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '11px', color: '#aaa', marginBottom: '6px' }}>Emotions:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {emotionCols.map(emotion => {
                  const isSelected = selectedEmotions.includes(emotion);
                  return (
                    <button
                      key={emotion}
                      onClick={() => {
                        setSelectedEmotions(prev => 
                          isSelected ? prev.filter(e => e !== emotion) : [...prev, emotion]
                        );
                      }}
                      style={{
                        padding: '4px 10px',
                        fontSize: '10px',
                        borderRadius: '4px',
                        border: '1px solid #444',
                        background: isSelected ? '#4ea1ff' : '#2a2a2a',
                        color: '#fff',
                        cursor: 'pointer'
                      }}
                    >
                      {emotion}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
          
          {stateKey && (
            <div>
              <div style={{ fontSize: '11px', color: '#aaa', marginBottom: '6px' }}>States:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', maxHeight: '100px', overflowY: 'auto' }}>
                {[...new Set(dataRows.map(r => r[stateKey]).filter(Boolean))].map(state => {
                  const isSelected = selectedStates.includes(state);
                  return (
                    <button
                      key={state}
                      onClick={() => {
                        setSelectedStates(prev => 
                          isSelected ? prev.filter(s => s !== state) : [...prev, state]
                        );
                      }}
                      style={{
                        padding: '4px 10px',
                        fontSize: '10px',
                        borderRadius: '4px',
                        border: '1px solid #444',
                        background: isSelected ? '#4ea1ff' : '#2a2a2a',
                        color: '#fff',
                        cursor: 'pointer'
                      }}
                    >
                      {state}
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      );
    };

    // Try each chart type in order until one works
    for (const tryChartType of chartTypesToTry) {
      // Radar Chart
      if (tryChartType === 'radar_chart' && emotionCols.length >= 3 && stateKey) {
        const emotionsToShow = selectedEmotions.length > 0 ? selectedEmotions : emotionCols;
        const statesToShow = selectedStates.length > 0 ? selectedStates : [...new Set(filteredRows.map(r => r[stateKey]).filter(Boolean))];
        
        const radarData = filteredRows
          .filter(row => statesToShow.includes(row[stateKey]))
          .slice(0, 5)
          .map(row => {
            const data = {};
            emotionsToShow.forEach(emotion => {
              const col = emotionToColumnMap[emotion] || emotion;
              data[emotion] = Number(row[col]) || 0;
            });
            return data;
          });
        
        const stateNames = filteredRows
          .filter(row => statesToShow.includes(row[stateKey]))
          .slice(0, 5)
          .map(row => (row[stateKey] || 'Unknown').substring(0, 12));
        
        const radarChartData = emotionsToShow.map(emotion => {
          const emotionData = { emotion: emotion.charAt(0).toUpperCase() + emotion.slice(1) };
          radarData.forEach((stateData, idx) => {
            const stateKeyForData = stateNames[idx]?.replace(/\s+/g, '_') || `state_${idx}`;
            emotionData[stateKeyForData] = stateData[emotion] || 0;
          });
          return emotionData;
        });
        
        return (
          <div>
            <FilterControls />
            <div style={{ width: '100%', height: '400px', padding: '10px 0' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarChartData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="emotion" tick={{ fill: '#bbb', fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, 1]} tick={{ fill: '#bbb', fontSize: 10 }} />
                {stateNames.map((stateName, idx) => {
                  const stateKeyForData = stateName.replace(/\s+/g, '_') || `state_${idx}`;
                  return (
                    <Radar
                      key={stateName || idx}
                      name={stateName || `State ${idx + 1}`}
                      dataKey={stateKeyForData}
                      stroke={colors[idx % colors.length]}
                      fill={colors[idx % colors.length]}
                      fillOpacity={0.3}
                      dot={{ r: 3 }}
                    />
                  );
                })}
                <Tooltip />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
            </div>
          </div>
        );
      }
      
      // Heatmap
      if (tryChartType === 'heatmap' && stateKey && emotionCols.length >= 3) {
        const heatmapData = dataRows.slice(0, 10).map(row => {
          const state = row[stateKey] || 'Unknown';
          const data = { state };
          Object.keys(emotionToColumnMap).forEach(emotion => {
            const col = emotionToColumnMap[emotion];
            data[emotion] = Number(row[col]) || 0;
          });
          return data;
        });

        return (
          <div style={{ width: '100%', height: '400px', padding: '10px 0' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={heatmapData} layout="vertical" margin={{ top: 20, right: 30, left: 80, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
                <XAxis type="number" domain={[0, 1]} tick={{ fill: '#bbb', fontSize: 11 }} />
                <YAxis dataKey="state" type="category" width={70} tick={{ fill: '#bbb', fontSize: 10 }} />
                <Tooltip />
                <Legend />
                {emotionCols.slice(0, 8).map((emotion, idx) => (
                  <Bar key={emotion} dataKey={emotion} stackId="a" fill={colors[idx % colors.length]} opacity={0.8} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }

      // Stacked Bar Chart
      if (tryChartType === 'stacked_bar_chart' && stateKey && numericCols.length >= 2) {
        const stackedData = dataRows.slice(0, 15).map(row => {
          const data = { state: (row[stateKey] || 'Unknown').substring(0, 12) };
          numericCols.slice(0, 6).forEach(col => {
            data[col] = Number(row[col]) || 0;
          });
          return data;
        });

        return (
          <div style={{ width: '100%', height: '350px', padding: '10px 0' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stackedData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
                <XAxis dataKey="state" angle={-45} textAnchor="end" height={80} tick={{ fill: '#bbb', fontSize: 10 }} />
                <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
                <Tooltip />
                <Legend />
                {numericCols.slice(0, 6).map((col, idx) => (
                  <Bar key={col} dataKey={col} stackId="a" fill={colors[idx % colors.length]} opacity={0.8} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }

      // Grouped Bar Chart
      if (tryChartType === 'grouped_bar_chart' && stateKey && numericCols.length >= 2) {
        const groupedData = dataRows.slice(0, 10).map(row => {
          const data = { state: (row[stateKey] || 'Unknown').substring(0, 10) };
          numericCols.slice(0, 4).forEach(col => {
            data[col] = Number(row[col]) || 0;
          });
          return data;
        });

        return (
          <div style={{ width: '100%', height: '350px', padding: '10px 0' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={groupedData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
                <XAxis dataKey="state" angle={-45} textAnchor="end" height={80} tick={{ fill: '#bbb', fontSize: 10 }} />
                <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
                <Tooltip />
                <Legend />
                {numericCols.slice(0, 4).map((col, idx) => (
                  <Bar key={col} dataKey={col} fill={colors[idx % colors.length]} opacity={0.8} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }

      // Multi-Line Chart
      if (tryChartType === 'multi_line_chart' && dateKey && numericCols.length >= 1) {
        if (numericCols.length > 1 && !stateKey) {
          const sorted = [...dataRows].sort((a, b) => new Date(a[dateKey]) - new Date(b[dateKey]));
          const metricsToShow = numericCols.slice(0, 6);

          return (
            <div style={{ width: '100%', height: '400px', padding: '10px 0' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sorted} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
                  <XAxis dataKey={dateKey} tick={{ fill: '#bbb', fontSize: 10 }} tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                  <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
                  <Tooltip labelFormatter={(v) => new Date(v).toLocaleDateString()} formatter={(v) => Number(v).toFixed(3)} />
                  <Legend />
                  {metricsToShow.map((metric, idx) => (
                    <Line key={metric} type="monotone" dataKey={metric} stroke={colors[idx % colors.length]} strokeWidth={2} dot={{ r: 3 }} name={metric} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          );
        }

        if (stateKey && numericCols.length >= 1) {
          const dataByDate = {};
          dataRows.forEach(row => {
            const date = row[dateKey];
            const state = row[stateKey] || 'Unknown';
            const metric = numericCols[0];
            if (!dataByDate[date]) {
              dataByDate[date] = { [dateKey]: date };
            }
            dataByDate[date][state] = Number(row[metric]) || 0;
          });

          const sortedData = Object.values(dataByDate).sort((a, b) => new Date(a[dateKey]) - new Date(b[dateKey]));
          const uniqueStates = [...new Set(dataRows.map(r => r[stateKey]).filter(Boolean))].slice(0, 10);

          return (
            <div style={{ width: '100%', height: '400px', padding: '10px 0' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={sortedData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
                  <XAxis dataKey={dateKey} tick={{ fill: '#bbb', fontSize: 10 }} tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                  <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
                  <Tooltip labelFormatter={(v) => new Date(v).toLocaleDateString()} formatter={(v) => Number(v).toFixed(3)} />
                  <Legend />
                  {uniqueStates.map((state, idx) => (
                    <Line key={state} type="monotone" dataKey={state} stroke={colors[idx % colors.length]} strokeWidth={2} dot={{ r: 3 }} name={state} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          );
        }
      }

      // Line Chart
      if (tryChartType === 'line_chart' && dateKey && numericCols.length >= 1) {
        const sorted = [...dataRows].sort((a, b) => new Date(a[dateKey]) - new Date(b[dateKey]));
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
                <XAxis dataKey={dateKey} tick={{ fill: '#bbb', fontSize: 10 }} tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
                <Tooltip labelFormatter={(v) => new Date(v).toLocaleDateString()} formatter={(v) => Number(v).toFixed(3)} />
                <Area type="monotone" dataKey={metric} stroke="#4ea1ff" fillOpacity={1} fill="url(#colorArea)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        );
      }

      // Horizontal Bar Chart
      if (tryChartType === 'horizontal_bar_chart' && numericCols.length >= 1) {
        const metric = numericCols[0];
        const categoryKey = stateKey || 'name';
        const sorted = [...dataRows].sort((a, b) => b[metric] - a[metric]).slice(0, 10);
        
        return (
          <div style={{ width: '100%', height: '350px', padding: '10px 0' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sorted} layout="vertical" margin={{ top: 20, right: 30, left: 80, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
                <XAxis type="number" tick={{ fill: '#bbb', fontSize: 11 }} />
                <YAxis dataKey={categoryKey} type="category" width={70} tick={{ fill: '#bbb', fontSize: 10 }} />
                <Tooltip />
                <Bar dataKey={metric} fill="#4ea1ff" opacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }

      // Bar Chart (Default)
      if (tryChartType === 'bar_chart' && numericCols.length >= 1) {
        const metric = numericCols[0];
        const categoryKey = stateKey || dateKey || cols.find(c => typeof rows[0][c] === 'string') || 'name';
        
        return (
          <div style={{ width: '100%', height: '350px', padding: '10px 0' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dataRows.slice(0, 20)} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" opacity={0.1} />
                <XAxis dataKey={categoryKey} angle={-45} textAnchor="end" height={80} tick={{ fill: '#bbb', fontSize: 10 }} interval={0} />
                <YAxis tick={{ fill: '#bbb', fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey={metric} fill="#4ea1ff" opacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      }
    }
    
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        Unable to visualize this data automatically.
      </div>
    );
  };

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button 
          className="chatbot-fab"
          onClick={() => setIsOpen(true)}
        >
          <span style={{ fontSize: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#4ea1ff' }}>
            <TrendingUp size={28} strokeWidth={2.5} />
          </span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="chatbot-floating-panel">
          <div className="chatbot-floating-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <TrendingUp size={20} strokeWidth={2.5} />
              <span style={{ fontWeight: '600' }}>TecVis 2.0 AI</span>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={clearHistory} className="chatbot-icon-btn" title="Clear History"><Trash2 size={16} /></button>
              <button onClick={() => setIsOpen(false)} className="chatbot-icon-btn"><X size={16} /></button>
            </div>
          </div>

          <div className="chatbot-floating-history">
            {history.length === 0 && (
              <div className="chatbot-welcome">
                <div className="welcome-icon">👋</div>
                <h4>Hi! I'm your AI analytics assistant.</h4>
                <p>Ask me about emotion trends, comparisons, or specific tweets.</p>
                
                <div className="example-queries">
                  <button className="example-query" onClick={() => setQuestion("Show me the trend of joy in Texas over the last 7 days")}>
                    📈 Show me the trend of joy in Texas over the last 7 days
                  </button>
                  <button className="example-query" onClick={() => setQuestion("Compare anger in California and Texas")}>
                    🆚 Compare anger in California and Texas
                  </button>
                  <button className="example-query" onClick={() => setQuestion("Show me the trend of anger/fear in New York")}>
                    🏆 Show me the trend of anger/fear in New York
                  </button>
                </div>
              </div>
            )}
            
            {history.map((msg, idx) => (
              <div key={idx} className="chat-message">
                {msg.type === 'question' && (
                  <div className="message-wrapper bot-wrapper">
                    <div className="message-icon user-icon"><User size={18} /></div>
                    <div className="message-bubble user-bubble">{msg.text}</div>
                  </div>
                )}
                
                {msg.type === 'answer' && (
                  <div className="message-wrapper bot-wrapper">
                    <div className="message-icon bot-icon"><Brain size={18} /></div>
                    <div className="message-bubble bot-bubble">
                      <div dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.message) }} />
                      
                      {/* SQL & Data Preview Button */}
                      {(msg.sql || (msg.rows && msg.rows.length > 0)) && (
                        <button 
                          className="view-analysis-btn"
                          onClick={() => openSqlModal(msg, idx)}
                        >
                          📊 View Analysis
                        </button>
                      )}
                    </div>
                  </div>
                )}
                
                {msg.type === 'status' && (
                  <div className="status-message">
                    <span className="status-dot"></span>
                    {msg.text}
                  </div>
                )}
                
                {msg.type === 'error' && (
                  <div className="error-message">
                    ⚠️ {msg.text}
                  </div>
                )}
              </div>
            ))}
            
            {loading && (
              <div className="chat-message">
                <div className="message-bubble bot-bubble">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
              </div>
            )}
          </div>

          <div className="chatbot-floating-footer">
            <div className="input-row">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    ask();
                  }
                }}
                placeholder="Ask a question about the data..."
                disabled={loading}
                autoFocus
                rows={1}
              />
              <button 
                onClick={ask} 
                disabled={loading || !question.trim()}
                className="send-btn"
              >
                ➤
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SQL & Data Modal */}
      {sqlModal && (
        <div className="sql-modal-overlay" onClick={closeSqlModal}>
          <div className="sql-modal-content" onClick={e => e.stopPropagation()}>
            <div className="sql-modal-header">
              <h3>Analysis Details</h3>
              <button onClick={closeSqlModal} className="close-modal-btn">✕</button>
            </div>
            
            <div className="sql-modal-body">
              {/* 1. Visualization Section (Microsoft Fabric Style) */}
              <div className="modal-section">
                <div 
                  className="section-header" 
                  onClick={() => setShowVisualization(!showVisualization)}
                  style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: '600' }}>Visualization</span>
                  </div>
                  <span style={{ fontSize: '12px', color: '#888' }}>
                    {showVisualization ? '▼' : '▶'}
                  </span>
                </div>
                
                {showVisualization && (
                  <div className="section-content">
                    {/* Reasoning Block */}
                    {sqlModal.chartReasoning && (
                      <div style={{ 
                        marginBottom: '16px', 
                        padding: '12px', 
                        background: 'rgba(78, 161, 255, 0.1)', 
                        borderLeft: '3px solid #4ea1ff',
                        borderRadius: '4px',
                        fontSize: '13px',
                        color: '#e0e0e0'
                      }}>
                        <strong>Why this chart?</strong> {sqlModal.chartReasoning}
                      </div>
                    )}

                    {/* Chart Preview */}
                    {showChartPreview ? (
                      <ChartRenderer 
                        rows={sqlModal.rows} 
                        hint={sqlModal.chartHint} 
                        config={sqlModal.chartConfig}
                        code={sqlModal.chartCode}
                      />
                    ) : (
                      <div style={{ padding: '20px', textAlign: 'center', color: '#888', border: '1px dashed #444', borderRadius: '8px' }}>
                        <button 
                          onClick={() => setShowChartPreview(true)}
                          style={{
                            padding: '8px 16px',
                            background: '#2a2a2a',
                            border: '1px solid #444',
                            borderRadius: '6px',
                            color: '#fff',
                            cursor: 'pointer'
                          }}
                        >
                          Load Chart
                        </button>
                      </div>
                    )}

                    {/* View Code Block */}
                    {sqlModal.chartCode && (
                      <div style={{ marginTop: '16px' }}>
                         <details>
                           <summary style={{ cursor: 'pointer', color: '#888', fontSize: '12px' }}>View Generated React Code</summary>
                           <pre style={{ 
                             background: '#111', 
                             padding: '12px', 
                             borderRadius: '6px', 
                             overflowX: 'auto', 
                             fontSize: '11px',
                             color: '#a5d6ff',
                             marginTop: '8px'
                           }}>
                             {sqlModal.chartCode}
                           </pre>
                         </details>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* 2. Data Table Section */}
              <div className="modal-section">
                <div 
                  className="section-header" 
                  onClick={() => setShowDataTable(!showDataTable)}
                  style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: '600' }}>Data Table ({sqlModal.rows ? sqlModal.rows.length : 0} rows)</span>
                  </div>
                  <span style={{ fontSize: '12px', color: '#888' }}>
                    {showDataTable ? '▼' : '▶'}
                  </span>
                </div>
                
                {showDataTable && sqlModal.rows && sqlModal.rows.length > 0 && (
                  <div className="section-content">
                    <div className="table-container">
                      <table>
                        <thead>
                          <tr>
                            {Object.keys(sqlModal.rows[0]).map(key => (
                              <th key={key}>{key}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {sqlModal.rows.slice(0, 100).map((row, i) => (
                            <tr key={i}>
                              {Object.values(row).map((val, j) => (
                                <td key={j}>
                                  {typeof val === 'object' && val !== null ? JSON.stringify(val) : String(val)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {sqlModal.rows.length > 100 && (
                        <div style={{ padding: '10px', textAlign: 'center', color: '#888', fontSize: '12px' }}>
                          Showing first 100 rows of {sqlModal.rows.length}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* 3. SQL Query Section */}
              <div className="modal-section">
                <div 
                  className="section-header" 
                  onClick={() => setShowSqlQuery(!showSqlQuery)}
                  style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: '600' }}>SQL Query</span>
                  </div>
                  <span style={{ fontSize: '12px', color: '#888' }}>
                    {showSqlQuery ? '▼' : '▶'}
                  </span>
                </div>
                
                {showSqlQuery && (
                  <div className="section-content" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <button 
                      className="copy-btn"
                      style={{ position: 'static', width: 'fit-content' }}
                      onClick={() => {
                        navigator.clipboard.writeText(sqlModal.sql);
                        setCopied(true);
                        setTimeout(() => setCopied(false), 2000);
                      }}
                    >
                      {copied ? '✓ Copied' : 'Copy SQL'}
                    </button>
                    <div className="sql-block">
                      <pre>{sqlModal.sql}</pre>
                    </div>
                  </div>
                )}
              </div>

            </div>
          </div>
        </div>
      )}
    </>
  );
}
