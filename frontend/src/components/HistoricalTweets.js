import React, { useState, useEffect } from 'react';
import './HistoricalTweets.css';

function HistoricalTweets() {
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedState, setSelectedState] = useState('');

  const fetchTweets = async (pageNum = 1, stateFilter = '') => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pageNum,
        limit: 20
      });
      
      if (stateFilter) {
        params.append('state', stateFilter);
      }

      const response = await fetch(`http://localhost:9000/tweets/history?${params}`);
      const data = await response.json();
      
      if (response.ok) {
        setTweets(data.tweets);
        setTotalPages(data.pagination.pages);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch tweets');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTweets(page, selectedState);
  }, [page, selectedState]);

  const handleStateFilter = (state) => {
    setSelectedState(state);
    setPage(1); // Reset to first page when filtering
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatEngagement = (likes, retweets, replies, views) => {
    return {
      likes: likes?.toLocaleString() || '0',
      retweets: retweets?.toLocaleString() || '0', 
      replies: replies?.toLocaleString() || '0',
      views: views?.toLocaleString() || '0'
    };
  };

  if (loading && tweets.length === 0) {
    return (
      <div className="historical-tweets">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading historical tweets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="historical-tweets">
      <div className="header">
        <h2>Tweet History</h2>
        <p>All generated tweets stored in database</p>
      </div>

      {/* State Filter */}
      <div className="filters">
        <select 
          value={selectedState} 
          onChange={(e) => handleStateFilter(e.target.value)}
          className="state-filter"
        >
          <option value="">All States</option>
          <option value="CA">California</option>
          <option value="NY">New York</option>
          <option value="TX">Texas</option>
          <option value="FL">Florida</option>
          <option value="WA">Washington</option>
          <option value="MA">Massachusetts</option>
        </select>
      </div>

      {error && (
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={() => fetchTweets(page, selectedState)}>
            Retry
          </button>
        </div>
      )}

      {/* Tweet List */}
      <div className="tweets-list">
        {tweets.map((tweet) => {
          const engagement = formatEngagement(tweet.likes, tweet.retweets, tweet.replies, tweet.views);
          
          return (
            <div key={`${tweet.id}-${tweet.created_at}`} className="tweet-card">
              <div className="tweet-header">
                <span className="username">@{tweet.username}</span>
                <span className="location">{tweet.state_code}</span>
                <span className="timestamp">{formatTimestamp(tweet.created_at)}</span>
              </div>
              
              <div className="tweet-content">
                <p>{tweet.raw_text}</p>
              </div>
              
              <div className="tweet-meta">
                <span className="context">#{tweet.context}</span>
              </div>
              
              <div className="tweet-stats">
                <span className="stat">{engagement.likes} likes</span>
                <span className="stat">{engagement.retweets} retweets</span>
                <span className="stat">{engagement.replies} replies</span>
                <span className="stat">{engagement.views} views</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button 
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
          >
            ← Previous
          </button>
          
          <span className="page-info">
            Page {page} of {totalPages}
          </span>
          
          <button 
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages || loading}
          >
            Next →
          </button>
        </div>
      )}

      {loading && tweets.length > 0 && (
        <div className="loading-overlay">
          <div className="spinner"></div>
        </div>
      )}
    </div>
  );
}

export default HistoricalTweets;
