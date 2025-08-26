import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import TweetDashboard from './components/TweetDashboard';

function App() {
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const eventSourceRef = useRef(null);

  useEffect(() => {
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
            return newTweets.slice(0, 50); // Keep only latest 50 tweets
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

    // Start connection
    connectEventSource();

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>🤖 Tech Tweet Stream</h1>
        <p>Real-time AI, GenAI, and Tech Innovation Updates</p>
        <div className="connection-status">
          <span className={`status-indicator ${connectionStatus}`}>
            {connectionStatus === 'connected' && '🟢 Connected'}
            {connectionStatus === 'connecting' && '🟡 Connecting...'}
            {connectionStatus === 'error' && '🔴 Error'}
          </span>
        </div>
      </header>

      <main className="App-main">
        <TweetDashboard
          tweets={tweets}
          loading={loading}
          error={error}
          connectionStatus={connectionStatus}
        />
      </main>
    </div>
  );
}

export default App;