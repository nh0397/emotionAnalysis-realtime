import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import Navigation from './components/Navigation';
import TweetDashboard from './components/TweetDashboard';
import HistoricalTweets from './components/HistoricalTweets';
import Analytics from './components/Analytics';
import EmotionVisualization from './components/EmotionVisualization';
import FloatingChatbot from './chatbot/FloatingChatbot';

function App() {
  const [currentPage, setCurrentPage] = useState('live');
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const eventSourceRef = useRef(null);

  useEffect(() => {
    // Only connect to SSE when on live page
    if (currentPage !== 'live') {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    const connectEventSource = () => {
      // Close existing connection if any
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Create new EventSource connection
      const eventSource = new EventSource('http://localhost:9000/tweets/stream');
      eventSourceRef.current = eventSource;

      // Handle different event types
      eventSource.addEventListener('connection', (event) => {
        console.log('SSE Connected:', event.data);
        setConnectionStatus('connected');
        setLoading(false);
        setError(null);
      });

      eventSource.addEventListener('tweet', (event) => {
        try {
          const tweet = JSON.parse(event.data);
          console.log('Received tweet:', tweet);
          setTweets(prevTweets => {
            const newTweets = [tweet, ...prevTweets];
            return newTweets.slice(0, 100); // Keep latest 100 tweets in memory
          });
        } catch (err) {
          console.error('Error parsing tweet:', err);
        }
      });

      eventSource.addEventListener('error', (event) => {
        try {
          const error = JSON.parse(event.data);
          console.error('Stream error:', error);
          setError(error.error);
        } catch (err) {
          console.error('Error parsing error event:', err);
          setError('Connection error');
        }
        setConnectionStatus('error');
      });

      // Handle connection errors
      eventSource.onerror = () => {
        console.error('SSE Connection error');
        setConnectionStatus('error');
        setError('Connection lost. Reconnecting...');
        
        // EventSource automatically tries to reconnect
        setConnectionStatus('connecting');
      };
    };

    // Start connection for live page
    connectEventSource();

    // Cleanup on unmount or page change
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [currentPage]);

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'live':
        return (
          <>
            <div className="page-header">
              <div className="connection-status">
                <span className={`status-indicator ${connectionStatus}`}>
                  {connectionStatus === 'connected' && 'Live Stream Active'}
                  {connectionStatus === 'connecting' && 'Connecting...'}
                  {connectionStatus === 'error' && 'Connection Error'}
                </span>
              </div>
            </div>
            <TweetDashboard
              tweets={tweets}
              loading={loading}
              error={error}
              connectionStatus={connectionStatus}
            />
          </>
        );
      case 'history':
        return <HistoricalTweets />;
      case 'metrics':
        return <Analytics />;
      case 'visualization':
        return <EmotionVisualization />;
      default:
        return <div>Page not found</div>;
    }
  };

  return (
    <div className="App">
      <Navigation 
        currentPage={currentPage} 
        onPageChange={setCurrentPage} 
      />
      
      <main className="App-main">
        {renderCurrentPage()}
      </main>

      <FloatingChatbot />
    </div>
  );
}

export default App;