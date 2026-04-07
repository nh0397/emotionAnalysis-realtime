import React, { useState, useEffect } from 'react';
import './Analytics.css';

function Analytics() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:9000/tweets/metrics');
      const data = await response.json();
      
      if (response.ok) {
        setMetrics(data);
        setError(null);
      } else {
        setError(data.error || 'Failed to fetch metrics');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    
    // Refresh metrics every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="analytics">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics">
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={fetchMetrics}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics">
      <div className="header">
        <h2>System Analytics</h2>
        <p>Real-time insights and metrics</p>
      </div>

      {/* Overview Cards */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value">{metrics.total_tweets.toLocaleString()}</div>
          <div className="metric-label">Total Tweets</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">{metrics.average_engagement.likes}</div>
          <div className="metric-label">Avg Likes</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">{metrics.average_engagement.retweets}</div>
          <div className="metric-label">Avg Retweets</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-value">{metrics.average_engagement.views}</div>
          <div className="metric-label">Avg Views</div>
        </div>
      </div>

      {/* Top States */}
      <div className="section">
        <h3>Top States by Tweet Volume</h3>
        <div className="list-container">
          {metrics.tweets_by_state.slice(0, 10).map((item, index) => (
            <div key={item.state} className="list-item">
              <span className="rank">#{index + 1}</span>
              <span className="name">{item.name} ({item.state})</span>
              <span className="count">{item.count} tweets</span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Keywords */}
      <div className="section">
        <h3>Trending Keywords</h3>
        <div className="list-container">
          {metrics.tweets_by_context.slice(0, 10).map((item, index) => (
            <div key={item.context} className="list-item">
              <span className="rank">#{index + 1}</span>
              <span className="name">{item.context}</span>
              <span className="count">{item.count} tweets</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity */}
      {metrics.hourly_activity.length > 0 && (
        <div className="section">
          <h3>Activity Last 24 Hours</h3>
          <div className="activity-chart">
            {metrics.hourly_activity.map((item, index) => {
              const maxCount = Math.max(...metrics.hourly_activity.map(h => h.count));
              const height = Math.max(5, (item.count / maxCount) * 100);
              const hour = new Date(item.hour).getHours();
              
              return (
                <div key={index} className="activity-bar">
                  <div 
                    className="bar" 
                    style={{ height: `${height}%` }}
                    title={`${hour}:00 - ${item.count} tweets`}
                  ></div>
                  <span className="hour-label">{hour}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="footer">
        <p>Last updated: {new Date(metrics.generated_at).toLocaleString()}</p>
        <button onClick={fetchMetrics} className="refresh-btn">
          Refresh
        </button>
      </div>
    </div>
  );
}

export default Analytics;
