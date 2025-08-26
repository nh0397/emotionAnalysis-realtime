import React from 'react';
import './TweetDashboard.css';

const TweetDashboard = ({ tweets, loading, error }) => {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
      return `${diffInSeconds}s`;
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes}m`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours}h`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const getSentimentColor = (sentiment) => {
    const colors = {
      excited: '#4CAF50',
      optimistic: '#8BC34A',
      impressed: '#2196F3',
      analytical: '#9C27B0',
      cautious: '#FFC107',
      skeptical: '#FF9800',
      concerned: '#F44336',
      critical: '#D32F2F'
    };
    return colors[sentiment] || '#757575';
  };

  if (loading) {
    return (
      <div className="tweet-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading tweets...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tweet-dashboard">
        <div className="error-container">
          <h3>⚠️ Error</h3>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="tweet-dashboard">
      <div className="dashboard-header">
        <h2>Latest Tech Tweets</h2>
        <div className="live-indicator">
          <span className="live-dot"></span>
          <span className="connection-badge">LIVE</span>
        </div>
      </div>

      <div className="tweet-feed">
        {tweets.length === 0 ? (
          <div className="empty-state">
            <h3>No tweets yet</h3>
            <p>Tech tweets will appear here as they are generated</p>
          </div>
        ) : (
          tweets.map((tweet, index) => (
            <div key={tweet.id || index} className="tweet-card">
              <div className="tweet-header">
                <div className="user-info">
                  <div className="avatar">
                    {tweet.username ? tweet.username.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <div className="user-details">
                    <span className="username">{tweet.username || 'Anonymous'}</span>
                    <span className="handle">@{tweet.username ? tweet.username.toLowerCase() : 'user'}</span>
                  </div>
                </div>
                <div className="tweet-meta">
                  {formatDate(tweet.timestamp || new Date())}
                </div>
              </div>

              <div className="tweet-content">
                {tweet.raw_text}
              </div>

              <div className="tweet-topic">
                <span className="topic-category">📌 {tweet.topic_category}</span>
                <span className="specific-topic">• {tweet.specific_topic}</span>
                <span 
                  className="sentiment-badge"
                  style={{ backgroundColor: getSentimentColor(tweet.sentiment) }}
                >
                  {tweet.sentiment}
                </span>
              </div>

              <div className="tweet-location">
                📍 {tweet.state_name} ({tweet.state_code})
              </div>

              <div className="tweet-stats">
                <div className="stat-item">
                  <svg viewBox="0 0 24 24">
                    <path d="M14.046 2.242l-4.148-.01h-.002c-4.374 0-7.8 3.427-7.8 7.802 0 4.098 3.186 7.206 7.465 7.37v3.828c0 .108.044.286.12.403.142.225.384.347.632.347.138 0 .277-.038.402-.118.264-.168 6.473-4.14 8.088-5.506 1.902-1.61 3.04-3.97 3.043-6.312v-.017c-.006-4.367-3.43-7.787-7.8-7.788zm3.787 12.972c-1.134.96-4.862 3.405-6.772 4.643V16.67c0-.414-.335-.75-.75-.75h-.396c-3.66 0-6.318-2.476-6.318-5.886 0-3.534 2.768-6.302 6.3-6.302l4.147.01h.002c3.532 0 6.3 2.766 6.302 6.296-.003 1.91-.942 3.844-2.514 5.176z"/>
                  </svg>
                  <span>{formatNumber(tweet.replies)}</span>
                </div>
                <div className="stat-item">
                  <svg viewBox="0 0 24 24">
                    <path d="M23.77 15.67c-.292-.293-.767-.293-1.06 0l-2.22 2.22V7.65c0-2.068-1.683-3.75-3.75-3.75h-5.85c-.414 0-.75.336-.75.75s.336.75.75.75h5.85c1.24 0 2.25 1.01 2.25 2.25v10.24l-2.22-2.22c-.293-.293-.768-.293-1.06 0s-.294.768 0 1.06l3.5 3.5c.145.147.337.22.53.22s.383-.072.53-.22l3.5-3.5c.294-.292.294-.767 0-1.06zm-10.66 3.28H7.26c-1.24 0-2.25-1.01-2.25-2.25V6.46l2.22 2.22c.148.147.34.22.532.22s.384-.073.53-.22c.293-.293.293-.768 0-1.06l-3.5-3.5c-.293-.294-.768-.294-1.06 0l-3.5 3.5c-.294.292-.294.767 0 1.06s.767.293 1.06 0l2.22-2.22V16.7c0 2.068 1.683 3.75 3.75 3.75h5.85c.414 0 .75-.336.75-.75s-.337-.75-.75-.75z"/>
                  </svg>
                  <span>{formatNumber(tweet.retweets)}</span>
                </div>
                <div className="stat-item">
                  <svg viewBox="0 0 24 24">
                    <path d="M12 21.638h-.014C9.403 21.59 1.95 14.856 1.95 8.478c0-3.064 2.525-5.754 5.403-5.754 2.29 0 3.83 1.58 4.646 2.73.814-1.148 2.354-2.73 4.645-2.73 2.88 0 5.404 2.69 5.404 5.755 0 6.376-7.454 13.11-10.037 13.157H12z"/>
                  </svg>
                  <span>{formatNumber(tweet.likes)}</span>
                </div>
                <div className="stat-item">
                  <svg viewBox="0 0 24 24">
                    <path d="M8.75 21V3h2v18h-2zM18 21V8.5h2V21h-2zM4 21l.004-10h2L6 21H4zm9.248 0v-7h2v7h-2z"/>
                  </svg>
                  <span>{formatNumber(tweet.views)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default TweetDashboard;