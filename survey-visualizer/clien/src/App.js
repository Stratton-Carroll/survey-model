import React, { useState, useEffect } from 'react';
import './App.css';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  ChartDataLabels
);

function App() {
  const [currentView, setCurrentView] = useState('tags'); // 'tags', 'tag-detail', 'responses', 'analytics', 'tag-editor'
  const [tags, setTags] = useState([]);
  const [selectedTag, setSelectedTag] = useState(null);
  const [responses, setResponses] = useState([]);
  const [questionsWithResponses, setQuestionsWithResponses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedQuestions, setExpandedQuestions] = useState(new Set());
  const [tagDistributions, setTagDistributions] = useState({});
  const [analytics, setAnalytics] = useState(null);
  const [selectedRoleCategory, setSelectedRoleCategory] = useState(null);
  const [selectedAnalyticsTag, setSelectedAnalyticsTag] = useState(null);
  const [selectedResponseForEditing, setSelectedResponseForEditing] = useState(null);
  const [availableTags, setAvailableTags] = useState([]);
  const [effectiveTags, setEffectiveTags] = useState([]);
  const [overrideStats, setOverrideStats] = useState(null);
  const [previousView, setPreviousView] = useState('tags');

  useEffect(() => {
    if (currentView === 'tags') {
      fetch('http://10.71.0.5:5000/api/tags')
        .then(response => response.json())
        .then(data => setTags(data))
        .catch(error => console.error('Error fetching tags:', error));
    } else if (currentView === 'responses') {
      setLoading(true);
      fetch('http://10.71.0.5:5000/api/responses')
        .then(response => response.json())
        .then(data => setQuestionsWithResponses(data))
        .catch(error => console.error('Error fetching responses:', error))
        .finally(() => setLoading(false));
    } else if (currentView === 'analytics') {
      setLoading(true);
      fetch('http://10.71.0.5:5000/api/analytics')
        .then(response => response.json())
        .then(data => setAnalytics(data))
        .catch(error => console.error('Error fetching analytics:', error))
        .finally(() => setLoading(false));
    } else if (currentView === 'tag-editor') {
      // Fetch override stats for tag editor
      fetch('http://10.71.0.5:5000/api/overrides/stats')
        .then(response => response.json())
        .then(data => setOverrideStats(data))
        .catch(error => console.error('Error fetching override stats:', error));
    }
  }, [currentView]);

  const handleTagClick = async (tag) => {
    setSelectedTag(tag);
    setCurrentView('tag-detail');
    setLoading(true);
    try {
      const response = await fetch(`http://10.71.0.5:5000/api/tags/${tag.TagID}/responses`);
      const data = await response.json();
      setResponses(data);
    } catch (error) {
      console.error('Error fetching responses:', error);
    }
    setLoading(false);
  };

  const handleBackClick = () => {
    setSelectedTag(null);
    setResponses([]);
    setCurrentView('tags');
  };

  const handleViewResponses = () => {
    setCurrentView('responses');
  };

  const handleViewTags = () => {
    setCurrentView('tags');
  };

  const handleViewAnalytics = () => {
    setCurrentView('analytics');
  };

  const handleTagEditor = () => {
    setCurrentView('tag-editor');
  };

  const handleBackFromTagEditor = () => {
    setSelectedResponseForEditing(null);
    setCurrentView(previousView);
  };

  const handleEditResponseTags = async (response) => {
    setPreviousView(currentView);
    setSelectedResponseForEditing(response);
    setCurrentView('tag-editor');
    setLoading(true);
    
    try {
      // Fetch available tags and current effective tags
      const [availableResponse, effectiveResponse] = await Promise.all([
        fetch('http://10.71.0.5:5000/api/tags/available'),
        fetch(`http://10.71.0.5:5000/api/response/${response.ResponseID}/tags`)
      ]);
      
      const availableData = await availableResponse.json();
      const effectiveData = await effectiveResponse.json();
      
      setAvailableTags(availableData);
      setEffectiveTags(effectiveData);
    } catch (error) {
      console.error('Error fetching tag data:', error);
    }
    
    setLoading(false);
  };

  const handleAddTag = async (tagId) => {
    try {
      const response = await fetch(`http://10.71.0.5:5000/api/response/${selectedResponseForEditing.ResponseID}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tag_id: tagId,
          action: 'ADD',
          applied_by: 'Policy Team Member',
          notes: 'Manual tag addition via UI'
        })
      });
      
      if (response.ok) {
        // Refresh effective tags
        const effectiveResponse = await fetch(`http://10.71.0.5:5000/api/response/${selectedResponseForEditing.ResponseID}/tags`);
        const effectiveData = await effectiveResponse.json();
        setEffectiveTags(effectiveData);
      }
    } catch (error) {
      console.error('Error adding tag:', error);
    }
  };

  const handleRemoveTag = async (tagId) => {
    try {
      const response = await fetch(`http://10.71.0.5:5000/api/response/${selectedResponseForEditing.ResponseID}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tag_id: tagId,
          action: 'REMOVE',
          applied_by: 'Policy Team Member',
          notes: 'Manual tag removal via UI'
        })
      });
      
      if (response.ok) {
        // Refresh effective tags
        const effectiveResponse = await fetch(`http://10.71.0.5:5000/api/response/${selectedResponseForEditing.ResponseID}/tags`);
        const effectiveData = await effectiveResponse.json();
        setEffectiveTags(effectiveData);
      }
    } catch (error) {
      console.error('Error removing tag:', error);
    }
  };

  const fetchTagDistribution = async (questionId) => {
    try {
      const response = await fetch(`http://10.71.0.5:5000/api/questions/${questionId}/tag-distribution`);
      const data = await response.json();
      setTagDistributions(prev => ({
        ...prev,
        [questionId]: data
      }));
    } catch (error) {
      console.error('Error fetching tag distribution:', error);
    }
  };

  const toggleQuestion = async (questionId) => {
    const newExpandedQuestions = new Set(expandedQuestions);
    if (newExpandedQuestions.has(questionId)) {
      newExpandedQuestions.delete(questionId);
    } else {
      newExpandedQuestions.add(questionId);
      if (!tagDistributions[questionId]) {
        await fetchTagDistribution(questionId);
      }
    }
    setExpandedQuestions(newExpandedQuestions);
  };

  const Logo = () => (
    <div className="logo-container">
      <img src="/hwhi-logo.png" alt="Heartland Whole Health Institute Logo" />
    </div>
  );

  // Highlighted Text Component
  const HighlightedText = ({ responseId, text, showLegend = true }) => {
    const [highlights, setHighlights] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
      if (responseId && text) {
        setLoading(true);
        fetch(`http://10.71.0.5:5000/api/response/${responseId}/highlight`)
          .then(response => response.json())
          .then(data => {
            if (data.highlights) {
              setHighlights(data.highlights);
            }
          })
          .catch(error => console.error('Error fetching highlights:', error))
          .finally(() => setLoading(false));
      }
    }, [responseId, text]);

    const getCategoryColor = (category, type) => {
      const colors = {
        'Clinical': { primary: '#e11d48', secondary: '#fda4af', context: '#fecdd3' },
        'Financial': { primary: '#059669', secondary: '#6ee7b7', context: '#d1fae5' },
        'Wellness': { primary: '#7c3aed', secondary: '#c4b5fd', context: '#ede9fe' },
        'Support': { primary: '#dc2626', secondary: '#fca5a5', context: '#fed7d7' },
        'Professional': { primary: '#0891b2', secondary: '#67e8f9', context: '#cffafe' },
        'Workforce': { primary: '#ea580c', secondary: '#fdba74', context: '#fed7aa' },
        'Regulatory': { primary: '#7c2d12', secondary: '#fbbf24', context: '#fef3c7' },
        'Geographic': { primary: '#166534', secondary: '#86efac', context: '#dcfce7' },
        'Profession': { primary: '#581c87', secondary: '#d8b4fe', context: '#f3e8ff' }
      };
      return colors[category]?.[type] || colors['Clinical'][type];
    };

    const renderHighlightedText = () => {
      if (!highlights.length) {
        return <span>{text}</span>;
      }

      // Sort highlights by start position and handle overlaps
      const sortedHighlights = [...highlights].sort((a, b) => a.start - b.start);
      const segments = [];
      let lastEnd = 0;

      sortedHighlights.forEach((highlight) => {
        // Add text before highlight
        if (highlight.start > lastEnd) {
          segments.push({
            text: text.substring(lastEnd, highlight.start),
            isHighlight: false
          });
        }

        // Add highlighted text (skip if overlapping)
        if (highlight.start >= lastEnd) {
          segments.push({
            text: text.substring(highlight.start, highlight.end),
            isHighlight: true,
            highlight: highlight
          });
          lastEnd = Math.max(lastEnd, highlight.end);
        }
      });

      // Add remaining text
      if (lastEnd < text.length) {
        segments.push({
          text: text.substring(lastEnd),
          isHighlight: false
        });
      }

      return segments.map((segment, index) => {
        if (segment.isHighlight) {
          const { highlight } = segment;
          const color = getCategoryColor(highlight.tag_category, highlight.type);
          return (
            <span
              key={index}
              className="keyword-highlight"
              style={{
                backgroundColor: color,
                padding: '2px 4px',
                borderRadius: '3px',
                margin: '0 1px',
                position: 'relative',
                borderLeft: `3px solid ${getCategoryColor(highlight.tag_category, 'primary')}`,
                fontWeight: highlight.type === 'primary' ? 'bold' : 'normal'
              }}
              title={`${highlight.tag_name} (${highlight.tag_category}) - ${highlight.type} keyword (score: ${highlight.score})`}
            >
              {segment.text}
            </span>
          );
        }
        return <span key={index}>{segment.text}</span>;
      });
    };

    const getLegendItems = () => {
      const uniqueTags = highlights.reduce((acc, highlight) => {
        const key = `${highlight.tag_name}-${highlight.tag_category}`;
        if (!acc[key]) {
          acc[key] = {
            tagName: highlight.tag_name,
            tagCategory: highlight.tag_category,
            types: new Set()
          };
        }
        acc[key].types.add(highlight.type);
        return acc;
      }, {});

      return Object.values(uniqueTags);
    };

    if (loading) {
      return <span className="highlight-loading">🔍 Analyzing keywords...</span>;
    }

    return (
      <div className="highlighted-text-container">
        <div className="highlighted-text">
          {renderHighlightedText()}
        </div>
        
        {showLegend && highlights.length > 0 && (
          <div className="highlight-legend">
            <div className="legend-header">
              <span className="legend-title">💡 AI Keyword Analysis</span>
              <span className="legend-subtitle">See why each tag was applied</span>
            </div>
            <div className="legend-items">
              {getLegendItems().map((item, index) => (
                <div key={index} className="legend-item">
                  <div 
                    className="legend-color" 
                    style={{ 
                      backgroundColor: getCategoryColor(item.tagCategory, 'secondary'),
                      borderLeft: `3px solid ${getCategoryColor(item.tagCategory, 'primary')}`
                    }}
                  ></div>
                  <span className="legend-text">
                    <strong>{item.tagName}</strong> ({item.tagCategory})
                    {Array.from(item.types).map(type => (
                      <span key={type} className={`keyword-type ${type}`}>
                        {type === 'primary' ? '🎯' : type === 'secondary' ? '📍' : '💡'}
                      </span>
                    ))}
                  </span>
                </div>
              ))}
            </div>
            <div className="legend-key">
              <span className="key-item">🎯 Primary keyword</span>
              <span className="key-item">📍 Secondary keyword</span>
              <span className="key-item">💡 Context keyword</span>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Tag Editor Component
  const TagEditor = () => {
    if (!selectedResponseForEditing) {
      return (
        <div className="tag-editor-home">
          <div className="editor-welcome">
            <div className="welcome-icon">🏷️</div>
            <h2>Tag Editor</h2>
            <p className="welcome-description">
              Select a response from any view and click "✏️ Edit Tags" to start editing tags manually.
            </p>
            {overrideStats && (
              <div className="override-stats-modern">
                <h3>Manual Tag Override Statistics</h3>
                <div className="stats-cards">
                  <div className="stat-card">
                    <div className="stat-number">{overrideStats.total_overrides}</div>
                    <div className="stat-label">Total Overrides</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-number">{overrideStats.additions}</div>
                    <div className="stat-label">Tags Added</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-number">{overrideStats.removals}</div>
                    <div className="stat-label">Tags Removed</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-number">{overrideStats.responses_modified}</div>
                    <div className="stat-label">Responses Modified</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }

    const effectiveTagIds = new Set(effectiveTags.map(tag => tag.TagID));
    const manuallyAddedTagIds = new Set(effectiveTags.filter(tag => tag.IsManuallyAdded).map(tag => tag.TagID));

    const groupedTags = availableTags.reduce((acc, tag) => {
      if (!acc[tag.TagCategory]) {
        acc[tag.TagCategory] = [];
      }
      acc[tag.TagCategory].push(tag);
      return acc;
    }, {});

    return (
      <div className="tag-editor-active">
        {/* Question Context - Always Visible */}
        <div className="question-context-sticky">
          <div className="context-header">
            <h3>Editing Response for Question ID {selectedResponseForEditing.QuestionID}:</h3>
            <p className="question-text">{selectedResponseForEditing.QuestionShort || selectedResponseForEditing.QuestionText}</p>
          </div>
        </div>

        {/* Response Context */}
        <div className="response-context-modern">
          <div className="response-card-editor">
            <div className="response-header-modern">
              <div className="response-meta-modern">
                <span className="response-id-badge">ID: {selectedResponseForEditing.ResponseID}</span>
                <span className="role-badge">{selectedResponseForEditing.RoleName}</span>
                <span className="location-badge">{selectedResponseForEditing.PrimaryCounty}</span>
                {selectedResponseForEditing.OrganizationName && (
                  <span className="org-badge">{selectedResponseForEditing.OrganizationName}</span>
                )}
              </div>
            </div>
            <div className="response-text-modern">
              <HighlightedText 
                responseId={selectedResponseForEditing.ResponseID} 
                text={selectedResponseForEditing.ResponseText}
                showLegend={true}
              />
            </div>
          </div>
        </div>

        {/* Tag Editing Interface */}
        <div className="tag-editing-modern">
          {/* Current Tags Section */}
          <div className="current-tags-section">
            <div className="section-header">
              <h4>🏷️ Current Tags ({effectiveTags.length})</h4>
              <div className="section-subtitle">Click × to remove a tag</div>
            </div>
            <div className="current-tags-grid">
              {effectiveTags.length === 0 ? (
                <div className="no-tags-message">
                  <span className="no-tags-icon">📝</span>
                  <p>No tags assigned yet. Add some tags below!</p>
                </div>
              ) : (
                effectiveTags.map((tag) => (
                  <div key={tag.TagID} className={`current-tag-pill ${manuallyAddedTagIds.has(tag.TagID) ? 'manually-added' : 'original'}`}>
                    <div className="tag-content">
                      <span className="tag-name">{tag.TagName}</span>
                      <span className="tag-category">{tag.TagCategory}</span>
                      {manuallyAddedTagIds.has(tag.TagID) && (
                        <span className="manual-indicator">✨ Manual</span>
                      )}
                    </div>
                    <button 
                      className="remove-tag-button"
                      onClick={() => handleRemoveTag(tag.TagID)}
                      title={`Remove "${tag.TagName}" tag`}
                    >
                      ×
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Available Tags Section */}
          <div className="available-tags-section">
            <div className="section-header">
              <h4>➕ Add Tags</h4>
              <div className="section-subtitle">Choose from available tags organized by category</div>
            </div>
            
            <div className="tag-categories-modern">
              {Object.entries(groupedTags).map(([category, tags]) => {
                const availableTagsInCategory = tags.filter(tag => !effectiveTagIds.has(tag.TagID));
                if (availableTagsInCategory.length === 0) return null;
                
                return (
                  <div key={category} className="tag-category-modern">
                    <div className="category-header">
                      <h5 className="category-name">{category}</h5>
                      <span className="category-count">({availableTagsInCategory.length} available)</span>
                    </div>
                    <div className="available-tags-grid">
                      {availableTagsInCategory.map((tag) => (
                        <button 
                          key={tag.TagID} 
                          className="available-tag-button"
                          onClick={() => handleAddTag(tag.TagID)}
                          title={tag.TagDescription || `Add "${tag.TagName}" tag`}
                        >
                          <div className="tag-button-content">
                            <span className="tag-name">{tag.TagName}</span>
                            <span className="add-icon">+</span>
                          </div>
                          {tag.TagDescription && (
                            <div className="tag-description">{tag.TagDescription}</div>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Tag Editor view
  if (currentView === 'tag-editor') {
    return (
      <div className="App">
        <Logo />
        <header className="App-header">
          <div className="nav-buttons">
            {selectedResponseForEditing ? (
              <button onClick={handleBackFromTagEditor} className="back-button">← Back to {previousView === 'tags' ? 'Tags' : previousView === 'responses' ? 'Responses' : previousView === 'analytics' ? 'Analytics' : 'Previous View'}</button>
            ) : (
              <button onClick={handleViewTags} className="back-button">← Back to Tags</button>
            )}
            <button onClick={handleViewResponses} className="nav-button">View All Responses</button>
            <button onClick={handleViewAnalytics} className="nav-button">Analytics</button>
          </div>
          <div className="page-title">
            <h1>Tag Editor</h1>
            <p className="page-description">Manually add or remove tags from survey responses</p>
          </div>
          
          {loading ? (
            <p>Loading tag editor...</p>
          ) : (
            <TagEditor />
          )}
        </header>
      </div>
    );
  }

  // Analytics view
  if (currentView === 'analytics') {
    return (
      <div className="App">
        <Logo />
        <header className="App-header">
          <div className="nav-buttons">
            <button onClick={handleViewTags} className="back-button">← Back to Tags</button>
            <button onClick={handleViewResponses} className="nav-button">View All Responses</button>
            <button onClick={handleTagEditor} className="nav-button">Tag Editor</button>
          </div>
          <div className="page-title">
            <h1>Survey Analytics Dashboard</h1>
            <p className="page-description">Comprehensive insights and metrics from the healthcare needs assessment survey</p>
          </div>
          
          {loading ? (
            <p>Loading analytics...</p>
          ) : analytics ? (
            <div className="analytics-dashboard">
              {/* Key Metrics Cards */}
              <div className="metrics-grid">
                <div className="metric-card">
                  <h3>Total Responses</h3>
                  <div className="metric-value">{analytics.overview?.total_responses || 'N/A'}</div>
                  <div className="metric-subtitle">Survey responses collected</div>
                </div>
                <div className="metric-card">
                  <h3>Unique Respondents</h3>
                  <div className="metric-value">{analytics.overview?.unique_respondents || 'N/A'}</div>
                  <div className="metric-subtitle">Individual participants</div>
                </div>
                <div className="metric-card">
                  <h3>Avg Response Rate</h3>
                  <div className="metric-value">{analytics.overview?.avg_response_rate ? `${Math.round(analytics.overview.avg_response_rate)}%` : 'N/A'}</div>
                  <div className="metric-subtitle">Across all questions</div>
                </div>
                <div className="metric-card">
                  <h3>Avg Words/Response</h3>
                  <div className="metric-value">{analytics.overview?.avg_word_count ? Math.round(analytics.overview.avg_word_count) : 'N/A'}</div>
                  <div className="metric-subtitle">Open-ended responses</div>
                </div>
              </div>

              {/* Role Category Distribution - Donut Chart */}
              {analytics.role_category_analysis && (
                <div className="charts-row">
                  <div className="chart-section half-width">
                    <h2>Total Responses by Role Category</h2>
                    <div className="chart-container donut-container">
                      <Doughnut
                        data={{
                          labels: analytics.role_category_analysis.map(role => role.RoleCategory),
                          datasets: [{
                            data: analytics.role_category_analysis.map(role => role.response_count),
                            backgroundColor: [
                              '#7a9944', '#3d6b7d', '#8b4513', '#483d8b', '#556b2f',
                              '#d2691e', '#800080', '#20b2aa', '#ff6347', '#4682b4', '#daa520'
                            ],
                            borderColor: '#3d003d',
                            borderWidth: 2,
                            hoverBorderWidth: 3
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            datalabels: {
                              display: false
                            },
                            legend: {
                              position: 'right',
                              labels: {
                                padding: 15,
                                usePointStyle: true,
                                font: {
                                  size: 12
                                }
                              }
                            },
                            tooltip: {
                              callbacks: {
                                label: (context) => {
                                  const total = analytics.role_category_analysis.reduce((sum, role) => sum + role.response_count, 0);
                                  const percentage = ((context.parsed / total) * 100).toFixed(1);
                                  return `${context.label}: ${context.parsed} (${percentage}%)`;
                                }
                              }
                            }
                          },
                          onClick: (_, elements) => {
                            if (elements.length > 0) {
                              const index = elements[0].index;
                              const roleCategory = analytics.role_category_analysis[index].RoleCategory;
                              setSelectedRoleCategory(selectedRoleCategory === roleCategory ? null : roleCategory);
                            }
                          }
                        }}
                        height={300}
                      />
                    </div>
                  </div>

                  {/* Tag Analysis - Filtered Bar Chart */}
                  <div className="chart-section half-width">
                    <h2>
                      Total Responses by Tag
                      {selectedRoleCategory && <span className="filter-indicator"> (Filtered by: {selectedRoleCategory})</span>}
                    </h2>
                    <div className="chart-container">
                      <Bar
                        data={{
                          labels: (selectedRoleCategory ? 
                            analytics.filtered_tag_analysis?.[selectedRoleCategory] || [] :
                            analytics.priority_areas || []
                          ).slice(0, 10).map(tag => tag.TagName),
                          datasets: [{
                            label: 'Tag Count',
                            data: (selectedRoleCategory ? 
                              analytics.filtered_tag_analysis?.[selectedRoleCategory] || [] :
                              analytics.priority_areas || []
                            ).slice(0, 10).map(tag => tag.ResponseCount || tag.count),
                            backgroundColor: selectedRoleCategory ? '#3d6b7d' : '#7a9944',
                            borderColor: '#3d003d',
                            borderWidth: 2,
                            borderRadius: 8
                          }]
                        }}
                        options={{
                          responsive: true,
                          maintainAspectRatio: false,
                          plugins: {
                            datalabels: {
                              display: false
                            },
                            legend: { display: false }
                          },
                          scales: {
                            y: { 
                              beginAtZero: true,
                              ticks: {
                                stepSize: 1
                              }
                            },
                            x: {
                              ticks: {
                                maxRotation: 45,
                                minRotation: 45,
                                font: {
                                  size: 11
                                }
                              }
                            }
                          }
                        }}
                        height={300}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Tag Analysis Section */}
              {analytics.priority_areas && (
                <div className="tag-analysis-section">
                  <h2>Tag Deep Dive Analysis</h2>
                  <p className="section-description">Click on any tag below to see which role categories mention it most frequently</p>
                  
                  <div className="charts-row">
                    {/* Clickable Tag List */}
                    <div className="chart-section half-width">
                      <h3>Top Healthcare Tags</h3>
                      <div className="tag-list-container">
                        {analytics.priority_areas.slice(0, 12).map((tag, index) => (
                          <div
                            key={tag.TagID}
                            className={`clickable-tag-item ${selectedAnalyticsTag?.TagID === tag.TagID ? 'selected' : ''}`}
                            onClick={() => setSelectedAnalyticsTag(selectedAnalyticsTag?.TagID === tag.TagID ? null : tag)}
                          >
                            <div className="tag-rank">#{index + 1}</div>
                            <div className="tag-info">
                              <h4>{tag.TagName}</h4>
                              <p>{tag.TagDescription}</p>
                              <span className="tag-count">{tag.ResponseCount} responses</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Tag Role Distribution Donut */}
                    <div className="chart-section half-width">
                      <h3>
                        {selectedAnalyticsTag ? `Role Distribution for "${selectedAnalyticsTag.TagName}"` : 'Select a Tag to View Role Distribution'}
                      </h3>
                      {selectedAnalyticsTag && analytics.tag_role_distribution?.[selectedAnalyticsTag.TagName] ? (
                        <div className="chart-container donut-container">
                          <Doughnut
                            data={{
                              labels: analytics.tag_role_distribution[selectedAnalyticsTag.TagName].map(role => role.RoleCategory),
                              datasets: [{
                                data: analytics.tag_role_distribution[selectedAnalyticsTag.TagName].map(role => role.ResponseCount),
                                backgroundColor: [
                                  '#7a9944', '#3d6b7d', '#8b4513', '#483d8b', '#556b2f',
                                  '#d2691e', '#800080', '#20b2aa', '#ff6347', '#4682b4', '#daa520'
                                ],
                                borderColor: '#3d003d',
                                borderWidth: 2,
                                hoverBorderWidth: 3
                              }]
                            }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              layout: {
                                padding: {
                                  top: 20,
                                  bottom: 20,
                                  left: 20,
                                  right: 20
                                }
                              },
                              plugins: {
                                legend: {
                                  display: true,
                                  position: 'top',
                                  maxHeight: 100,
                                  labels: {
                                    padding: 12,
                                    usePointStyle: true,
                                    pointStyle: 'circle',
                                    font: {
                                      size: 10,
                                      family: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
                                    },
                                    color: '#374151',
                                    boxWidth: 8,
                                    boxHeight: 8,
                                    generateLabels: (chart) => {
                                      const data = chart.data;
                                      if (data.labels.length && data.datasets.length) {
                                        return data.labels.map((label, i) => {
                                          const value = data.datasets[0].data[i];
                                          const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                          const percentage = ((value / total) * 100).toFixed(1);
                                          
                                          return {
                                            text: `${label} (${percentage}%)`,
                                            fillStyle: data.datasets[0].backgroundColor[i],
                                            strokeStyle: data.datasets[0].backgroundColor[i],
                                            lineWidth: 0,
                                            pointStyle: 'circle',
                                            hidden: false,
                                            index: i
                                          };
                                        });
                                      }
                                      return [];
                                    }
                                  }
                                },
                                tooltip: {
                                  enabled: false
                                }
                              }
                            }}
                            height={600}
                          />
                        </div>
                      ) : (
                        <div className="empty-chart-placeholder">
                          <div className="placeholder-content">
                            <div className="placeholder-icon">📊</div>
                            <p>Click on a tag from the list to see which role categories mention it most</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Response Quality Insights */}
              {analytics.response_quality && (
                <div className="insights-section">
                  <h2>Response Quality Insights</h2>
                  <div className="insights-grid">
                    <div className="insight-card">
                      <h4>High Engagement Questions</h4>
                      <p>Questions with response rates above 80%</p>
                      <div className="insight-value">{analytics.response_quality.high_engagement_count || 0} questions</div>
                    </div>
                    <div className="insight-card">
                      <h4>Detailed Responses</h4>
                      <p>Responses with 50+ words</p>
                      <div className="insight-value">{analytics.response_quality.detailed_responses_count || 0} responses</div>
                    </div>
                    <div className="insight-card">
                      <h4>Text vs Scale Questions</h4>
                      <p>Open-ended vs structured questions</p>
                      <div className="insight-value">{analytics.response_quality.text_question_ratio || 'N/A'}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Top Priority Areas */}
              {analytics.priority_areas && (
                <div className="insights-section">
                  <h2>Top Priority Healthcare Areas</h2>
                  <div className="priority-list">
                    {analytics.priority_areas.slice(0, 5).map((area, index) => (
                      <div key={index} className="priority-item">
                        <div className="priority-rank">#{index + 1}</div>
                        <div className="priority-content">
                          <h4>{area.TagName}</h4>
                          <p>{area.TagDescription}</p>
                          <span className="priority-count">{area.ResponseCount} mentions</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p>No analytics data available</p>
          )}
        </header>
      </div>
    );
  }

  // Tag detail view
  if (currentView === 'tag-detail' && selectedTag) {
    return (
      <div className="App">
        <Logo />
        <header className="App-header">
          <div className="nav-buttons">
            <button onClick={handleBackClick} className="back-button">← Back to Tags</button>
            <button onClick={handleViewResponses} className="nav-button">View All Responses</button>
            <button onClick={handleViewAnalytics} className="nav-button">Analytics</button>
            <button onClick={handleTagEditor} className="nav-button">Tag Editor</button>
          </div>
          <h1>{selectedTag.TagName}</h1>
          <p className="tag-info">
            Category: {selectedTag.TagCategory} | {selectedTag.ResponseCount} responses
          </p>
          {loading ? (
            <p>Loading responses...</p>
          ) : (
            <div className="responses">
              {responses.map((response, index) => (
                <div key={index} className="response-wrapper">
                  <div className="question-context">
                    <span className="question-label">Question:</span>
                    <span className="question-text">{response.QuestionShort}</span>
                  </div>
                  <div className="full-response-card">
                    <div className="response-header">
                      <div className="response-meta">
                        <span className="response-id">ID: {response.ResponseID}</span>
                        <span className="role">{response.RoleName}</span>
                        <span className="location">{response.PrimaryCounty}</span>
                        {response.OrganizationName && (
                          <span className="org-type">{response.OrganizationName}</span>
                        )}
                      </div>
                      <button 
                        className="edit-tags-btn"
                        onClick={() => handleEditResponseTags(response)}
                        title="Edit tags for this response"
                      >
                        ✏️ Edit Tags
                      </button>
                    </div>
                    <div className="response-content">
                      <div className="response-text">
                        <HighlightedText 
                          responseId={response.ResponseID} 
                          text={response.ResponseText}
                          showLegend={false}
                        />
                      </div>
                      <div className="response-tags">
                        <div className="tags-list">
                          {response.Tags && response.Tags.map((tag, tagIndex) => (
                            <span 
                              key={tagIndex} 
                              className={`tag-badge ${tag.TagCategory ? tag.TagCategory.toLowerCase() : ''}`}
                            >
                              {tag.TagName}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </header>
      </div>
    );
  }

  // Responses view
  if (currentView === 'responses') {
    return (
      <div className="App">
        <header className="App-header">
          <div className="nav-buttons">
            <button onClick={handleViewTags} className="back-button">← Back to Tags</button>
            <button onClick={handleViewAnalytics} className="nav-button">Analytics</button>
            <button onClick={handleTagEditor} className="nav-button">Tag Editor</button>
          </div>
          <div className="questions-container">
            {loading ? (
              <p>Loading responses...</p>
            ) : (
              questionsWithResponses.map(question => (
                <div key={question.QuestionID} className="question-section">
                  <div
                    className="question-header clickable"
                    onClick={() => toggleQuestion(question.QuestionID)}
                  >
                    <div className="question-header-content">
                      <h2>Q{question.QuestionID}: {question.QuestionShort}</h2>
                      <p className="question-full">{question.QuestionText}</p>
                      <span className="response-count">{question.responses.length} responses</span>
                    </div>
                    <div className="expand-icon">
                      {expandedQuestions.has(question.QuestionID) ? '−' : '+'}
                    </div>
                  </div>
                  
                  {expandedQuestions.has(question.QuestionID) && (
                    <div className="question-responses">
                      {tagDistributions[question.QuestionID] && (
                        <div className="tag-distribution-chart">
                          <Bar
                            data={{
                              labels: tagDistributions[question.QuestionID].map(tag => tag.TagName),
                              datasets: [{
                                label: 'Responses',
                                data: tagDistributions[question.QuestionID].map(tag => tag.TagCount),
                                backgroundColor: '#7a9944',
                                borderColor: '#3d003d',
                                borderWidth: 2,
                                borderRadius: 6,
                                barThickness: 'flex',
                                maxBarThickness: 50
                              }]
                            }}
                            options={{
                              responsive: true,
                              maintainAspectRatio: false,
                              layout: {
                                padding: {
                                  top: 10,
                                  bottom: 25,
                                  left: 10,
                                  right: 10
                                }
                              },
                              plugins: {
                                legend: {
                                  display: false
                                },
                                title: {
                                  display: false
                                },
                                tooltip: {
                                  callbacks: {
                                    title: (tooltipItems) => {
                                      const index = tooltipItems[0].dataIndex;
                                      return tagDistributions[question.QuestionID][index].TagName;
                                    }
                                  }
                                }
                              },
                              scales: {
                                x: {
                                  ticks: {
                                    color: 'rgba(255, 255, 255, 0.95)',
                                    font: {
                                      size: 11,
                                      weight: '500'
                                    },
                                    maxRotation: 45,
                                    minRotation: 45,
                                    padding: 15,
                                    autoSkip: false,
                                    textOverflow: 'show'
                                  },
                                  grid: {
                                    display: false
                                  }
                                },
                                y: {
                                  beginAtZero: true,
                                  suggestedMax: Math.max(...tagDistributions[question.QuestionID].map(tag => tag.TagCount)) * 1.1,
                                  ticks: {
                                    color: 'rgba(255, 255, 255, 0.95)',
                                    font: {
                                      size: 12,
                                      weight: '500'
                                    },
                                    padding: 8,
                                    stepSize: 1
                                  },
                                  grid: {
                                    display: true,
                                    color: 'rgba(0, 0, 0, 0.08)',
                                    drawBorder: false,
                                    lineWidth: 1
                                  },
                                  border: {
                                    display: false
                                  }
                                }
                              },
                              animation: {
                                duration: 750,
                                easing: 'easeOutQuart'
                              },
                              barThickness: 'flex',
                              maxBarThickness: 50
                            }}
                            style={{ height: '400px', marginBottom: '20px' }}
                          />
                        </div>
                      )}
                      {question.responses.map((response) => (
                        <div key={response.ResponseID} className="full-response-card">
                          <div className="response-header">
                            <div className="response-meta">
                              <span className="response-id">ID: {response.ResponseID}</span>
                              <span className="role">{response.RoleName}</span>
                              <span className="location">{response.PrimaryCounty}</span>
                              {response.OrganizationName && (
                                <span className="org-type">{response.OrganizationName}</span>
                              )}
                            </div>
                            <button 
                              className="edit-tags-btn"
                              onClick={() => handleEditResponseTags(response)}
                              title="Edit tags for this response"
                            >
                              ✏️ Edit Tags
                            </button>
                          </div>
                          <div className="response-content">
                            <div className="response-text">
                              <HighlightedText 
                                responseId={response.ResponseID} 
                                text={response.ResponseText}
                                showLegend={false}
                              />
                            </div>
                            <div className="response-tags">
                              <div className="tags-list">
                                {response.Tags && response.Tags.map((tag, tagIndex) => (
                                  <span 
                                    key={tagIndex} 
                                    className={`tag-badge ${tag.TagCategory ? tag.TagCategory.toLowerCase() : ''}`}
                                  >
                                    {tag.TagName}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </header>
      </div>
    );
  }

  // Main tags view
  return (
    <div className="App">
      <Logo />
      <header className="App-header">
        <div className="nav-buttons">
          <button onClick={handleViewResponses} className="nav-button">View All Responses</button>
          <button onClick={handleViewAnalytics} className="nav-button">Analytics</button>
          <button onClick={handleTagEditor} className="nav-button">Tag Editor</button>
        </div>
        <div className="page-title">
          <h1>Healthcare Survey Analysis</h1>
          <p className="page-description">Explore healthcare challenges and insights through our comprehensive survey analysis. Click on any category to dive deeper into specific responses.</p>
        </div>
        <div className="tags-grid">
          {tags.map(tag => (
            <div key={tag.TagID} className="tag-card" onClick={() => handleTagClick(tag)}>
              <div className="tag-meta">
                <span className="category">{tag.TagCategory}</span>
                <span className="count">{tag.ResponseCount} responses</span>
              </div>
              <h3>{tag.TagName}</h3>
              <p className="description">{tag.TagDescription}</p>
            </div>
          ))}
        </div>
      </header>
    </div>
  );
}

export default App;
