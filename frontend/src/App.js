import React, { useState, useEffect } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState('');
  const [queryHistory, setQueryHistory] = useState([]);

  // Sample Malayalam agricultural queries for demonstration
  const sampleQueries = [
    'എന്റെ നെല്ല് വിളയിൽ പുഴുക്കൾ വന്നിട്ടുണ്ട്. എന്ത് ചെയ്യണം?',
    'തെങ്ങിന് എന്ത് വളം ഇടണം?',
    'കുരുമുളകിന്റെ രോഗത്തിന് ചികിത്സ എന്താണ്?',
    'മഴക്കാലത്ത് നടാൻ പറ്റിയ വിളകൾ ഏതൊക്കെ?',
    'കപ്പ നടാനുള്ള നല്ല സമയം എപ്പോഴാണ്?'
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');
    setResponse(null);

    try {
      const response = await fetch(`${BACKEND_URL}/api/farmer-query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: query,
          query_type: 'general',
          location: location || null,
          farmer_id: 'demo_farmer'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResponse(data);
      
      // Add to history
      setQueryHistory(prev => [{
        id: data.id,
        query: query,
        timestamp: new Date().toLocaleString(),
        status: data.status
      }, ...prev.slice(0, 4)]); // Keep only last 5 queries

    } catch (err) {
      console.error('Error:', err);
      setError(`Failed to process query: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSampleQuery = (sampleQuery) => {
    setQuery(sampleQuery);
  };

  const formatRecommendations = (recommendations) => {
    if (!recommendations || recommendations.length === 0) return null;
    
    return recommendations.map((rec, index) => (
      <div key={index} className="recommendation-item">
        <div className="rec-content">{rec}</div>
      </div>
    ));
  };

  return (
    <div className="App">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo">🌾</div>
            <div>
              <h1>Digital Krishi Officer</h1>
              <p>ഡിജിറ്റൽ കൃഷി ഓഫീസർ - AI-Powered Agricultural Assistant</p>
            </div>
          </div>
          <div className="status-indicator">
            <span className="status-dot active"></span>
            <span>System Active</span>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
          {/* Introduction Section */}
          <section className="intro-section">
            <h2>Welcome to Your Digital Agricultural Assistant</h2>
            <p>Ask your farming questions in Malayalam and get expert advice powered by AI agents</p>
            <div className="features">
              <div className="feature">
                <span className="feature-icon">🔍</span>
                <span>Query Understanding</span>
              </div>
              <div className="feature">
                <span className="feature-icon">🌐</span>
                <span>Malayalam Translation</span>
              </div>
              <div className="feature">
                <span className="feature-icon">🧠</span>
                <span>Expert Agricultural Advice</span>
              </div>
              <div className="feature">
                <span className="feature-icon">📊</span>
                <span>Multi-Agent Analysis</span>
              </div>
            </div>
          </section>

          {/* Sample Queries */}
          <section className="sample-queries">
            <h3>Sample Questions (നമുന്ന ചോദ്യങ്ങൾ)</h3>
            <div className="sample-grid">
              {sampleQueries.map((sample, index) => (
                <button 
                  key={index}
                  className="sample-query-btn"
                  onClick={() => handleSampleQuery(sample)}
                >
                  {sample}
                </button>
              ))}
            </div>
          </section>

          {/* Query Form */}
          <section className="query-section">
            <form onSubmit={handleSubmit} className="query-form">
              <div className="form-group">
                <label htmlFor="query">Your Agricultural Question (മലയാളത്തിൽ ചോദിക്കാം)</label>
                <textarea
                  id="query"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="എന്റെ കൃഷിയിലുണ്ടായ പ്രശ്നം... (Type your farming question in Malayalam)"
                  rows="4"
                  className="query-input"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="location">Farm Location (Optional)</label>
                <input
                  id="location"
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g., Kottayam, Alappuzha, Thrissur..."
                  className="location-input"
                />
              </div>

              <button 
                type="submit" 
                className="submit-btn"
                disabled={isLoading || !query.trim()}
              >
                {isLoading ? (
                  <>
                    <span className="spinner"></span>
                    Processing... പ്രോസസ്സിംഗ്...
                  </>
                ) : (
                  'Get Agricultural Advice - കൃഷി സഹായം ലഭിക്കാൻ'
                )}
              </button>
            </form>
          </section>

          {/* Error Display */}
          {error && (
            <section className="error-section">
              <div className="error-card">
                <span className="error-icon">⚠️</span>
                <div>
                  <h4>Error</h4>
                  <p>{error}</p>
                </div>
              </div>
            </section>
          )}

          {/* Response Display */}
          {response && (
            <section className="response-section">
              <div className="response-container">
                <div className="response-header">
                  <h3>🎯 Agricultural Advice & Analysis</h3>
                  <div className="response-meta">
                    <span className="query-id">ID: {response.id}</span>
                    <span className="status-badge success">
                      {response.status === 'completed' ? '✅ Completed' : '⏳ Processing'}
                    </span>
                  </div>
                </div>

                {/* Original Query */}
                <div className="response-card">
                  <h4>📝 Your Question</h4>
                  <p className="original-text">{response.original_text}</p>
                </div>

                {/* Translation */}
                {response.translated_text && (
                  <div className="response-card">
                    <h4>🌐 English Translation</h4>
                    <p className="translated-text">{response.translated_text}</p>
                  </div>
                )}

                {/* Query Analysis */}
                {response.intent && (
                  <div className="response-card">
                    <h4>🔍 Query Analysis</h4>
                    <div className="analysis-grid">
                      <div className="analysis-item">
                        <span className="label">Intent:</span>
                        <span className="value intent-badge">{response.intent}</span>
                      </div>
                      {response.confidence && (
                        <div className="analysis-item">
                          <span className="label">Confidence:</span>
                          <span className="value">{Math.round(response.confidence * 100)}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {response.recommendations && response.recommendations.length > 0 && (
                  <div className="response-card recommendations">
                    <h4>🌱 Expert Recommendations</h4>
                    <div className="recommendations-content">
                      {formatRecommendations(response.recommendations)}
                    </div>
                  </div>
                )}

                {/* Agent Responses */}
                {response.agent_responses && (
                  <div className="response-card">
                    <h4>🤖 Agent Processing Details</h4>
                    <div className="agent-details">
                      {response.agent_responses.translation && (
                        <div className="agent-item">
                          <strong>Translation Agent:</strong>
                          <span className={`agent-status ${response.agent_responses.translation.success ? 'success' : 'error'}`}>
                            {response.agent_responses.translation.success ? '✅ Success' : '❌ Failed'}
                          </span>
                        </div>
                      )}
                      {response.agent_responses.analysis && (
                        <div className="agent-item">
                          <strong>Query Analysis Agent:</strong>
                          <span className="agent-status success">✅ Completed</span>
                        </div>
                      )}
                      {response.agent_responses.advice && (
                        <div className="agent-item">
                          <strong>Agriculture Advisor Agent:</strong>
                          <span className={`agent-status ${response.agent_responses.advice.success ? 'success' : 'error'}`}>
                            {response.agent_responses.advice.success ? '✅ Advice Generated' : '❌ Failed'}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Query History */}
          {queryHistory.length > 0 && (
            <section className="history-section">
              <h3>📊 Recent Queries</h3>
              <div className="history-list">
                {queryHistory.map((item, index) => (
                  <div key={item.id} className="history-item">
                    <div className="history-query">{item.query.substring(0, 100)}...</div>
                    <div className="history-meta">
                      <span className="history-time">{item.timestamp}</span>
                      <span className={`history-status ${item.status}`}>
                        {item.status === 'completed' ? '✅' : '⏳'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <p>© 2025 Digital Krishi Officer - Empowering farmers with AI technology</p>
          <p>Supporting Malayalam-speaking agricultural communities</p>
        </div>
      </footer>
    </div>
  );
}

export default App;