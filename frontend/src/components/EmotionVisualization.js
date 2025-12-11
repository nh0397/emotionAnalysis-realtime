import React, { Component } from 'react';
import SimpleDotPlot from './SimpleDotPlot';
import './EmotionVisualization.css';

const dimensions = {
  width: 1000,
  height: 900,
  margin: { top: 30, right: 350, bottom: 60, left: 300 }
};

const emotionColorsObjects = [
  { emotion: 'anger', color: '#FF0000' },
  { emotion: 'fear', color: '#FFA500' },
  { emotion: 'positive', color: '#008000' },
  { emotion: 'sadness', color: '#0000FF' },
  { emotion: 'surprise', color: '#FFC0CB' },
  { emotion: 'joy', color: '#FFD700' },
  { emotion: 'anticipation', color: '#9400D3' },
  { emotion: 'trust', color: '#00FFFF' },
  { emotion: 'negative', color: '#A9A9A9' },
  { emotion: 'disgust', color: '#808000' }
];

class EmotionVisualization extends Component {

  constructor(props) {
    super(props);
    this.state = { 
      data: [], 
      loading: true, 
      error: null,
      lastUpdated: null
    };
  }

  componentDidMount() {
    console.log("🎯 EmotionVisualization mounted - loading data...");
    this.loadData();
    
    // REAL-TIME: Auto-refresh every 30 seconds (optimized for performance)
    this.interval = setInterval(() => {
      this.loadData();
    }, 30000);
  }

  componentWillUnmount() {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }

  loadData = () => {
    this.setState({ loading: true, error: null });
    
    this.callBackendAPI()
    .then((data) => {
      console.log(`📊 Data loaded: ${data.length} states`);
      
      this.setState({ 
        data: data, 
        loading: false,
        lastUpdated: new Date()
      });
    })
    .catch(err => {
      console.error('❌ Error loading visualization data:', err);
      this.setState({ 
        error: err.message,
        loading: false
      });
    });
  }
  
  callBackendAPI = async () => {
    const response = await fetch('http://localhost:9000/data');
    const body = await response.json();

    if (response.status !== 200) {
      throw Error(body.message || 'Failed to fetch aggregated data')
    }
    return body;
  };


  render() {
    const { data, loading, error, lastUpdated } = this.state;
    
    return (
      <div className="emotion-visualization">
        
        {/* Header with Real-time Status */}
        <div className="header">
          <h2>Real-time Emotion Analysis by State</h2>
          <div className="controls">
            <button onClick={this.loadData} className="refresh-btn" disabled={loading}>
              {loading ? 'Updating...' : 'Refresh Now'}
            </button>
            {lastUpdated && (
              <span className="last-updated">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-message">
            <p>Error loading data: {error}</p>
            <button onClick={this.loadData}>Retry</button>
          </div>
        )}

        {/* Loading State */}
        {loading && data.length === 0 && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Loading real-time emotion data...</p>
          </div>
        )}

        {/* Main Visualization */}
        {data.length > 0 && (
          <div className="visualization-container">
            <div className="chart-section">
              <h3>Interactive Dot Plot Chart</h3>
              <p>Real-time emotion scores by state • Updates every 30 seconds</p>
              
              
              <div className="dot-plot-chart">
                <SimpleDotPlot
                  data={data}
                  dimensions={dimensions}
                  colorObjects={emotionColorsObjects}
                />
              </div>
            </div>
          </div>
        )}

        {/* Real-time Indicator */}
        {!loading && data.length > 0 && (
          <div style={{ 
            position: 'fixed', 
            bottom: window.innerWidth <= 768 ? '80px' : '20px', 
            left: window.innerWidth <= 768 ? '20px' : 'auto',
            right: window.innerWidth <= 768 ? 'auto' : '90px', 
            background: 'rgba(0,0,0,0.8)', 
            color: 'white', 
            padding: '10px 15px', 
            borderRadius: '20px',
            fontSize: '12px',
            border: '1px solid rgba(255,255,255,0.2)',
            zIndex: 9997
          }}>
            🔴 LIVE • {data.length} states • Next update in {Math.ceil((30000 - (Date.now() - lastUpdated?.getTime() || 0)) / 1000)}s
          </div>
        )}
      </div>
    );
  }
}

export default EmotionVisualization;
