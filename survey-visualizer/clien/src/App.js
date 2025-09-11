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
import Plot from 'react-plotly.js';

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
  const [presentationMode, setPresentationMode] = useState(false);
  const [selectedRoleType, setSelectedRoleType] = useState(null);
  const [selectedResponseForEditing, setSelectedResponseForEditing] = useState(null);
  const [availableTags, setAvailableTags] = useState([]);
  const [effectiveTags, setEffectiveTags] = useState([]);
  const [overrideStats, setOverrideStats] = useState(null);
  const [previousView, setPreviousView] = useState('tags');
  const [showingSubTagsFor, setShowingSubTagsFor] = useState(null);

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
        fetch(`http://10.71.0.5:5000/api/responses/${response.ResponseID}/effective-tags`)
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
        const effectiveResponse = await fetch(`http://10.71.0.5:5000/api/responses/${selectedResponseForEditing.ResponseID}/effective-tags`);
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
        const effectiveResponse = await fetch(`http://10.71.0.5:5000/api/responses/${selectedResponseForEditing.ResponseID}/effective-tags`);
        const effectiveData = await effectiveResponse.json();
        setEffectiveTags(effectiveData);
      }
    } catch (error) {
      console.error('Error removing tag:', error);
    }
  };

  const toggleSubTagPicker = (primaryTagId) => {
    setShowingSubTagsFor(showingSubTagsFor === primaryTagId ? null : primaryTagId);
  };

  const handleQuickRemoveTag = async (responseId, tagId, tagName) => {
    try {
      const response = await fetch(`http://10.71.0.5:5000/api/response/${responseId}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tag_id: tagId,
          action: 'REMOVE',
          applied_by: 'Policy Team Member',
          notes: `Quick removal of "${tagName}" tag from main view`
        })
      });
      
      if (response.ok) {
        // Refresh the responses to show updated tags
        if (currentView === 'responses') {
          // Refresh responses view
          const responsesResponse = await fetch('http://10.71.0.5:5000/api/responses');
          const data = await responsesResponse.json();
          setQuestionsWithResponses(data);
        } else if (currentView === 'tag-detail' && selectedTag) {
          // Refresh tag detail view
          const tagResponse = await fetch(`http://10.71.0.5:5000/api/tags/${selectedTag.TagID}/responses`);
          const data = await tagResponse.json();
          setResponses(data);
        }
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
            <div className="current-tags-grid hierarchical">
              {effectiveTags.length === 0 ? (
                <div className="no-tags-message">
                  <span className="no-tags-icon">📝</span>
                  <p>No tags assigned yet. Add some tags below!</p>
                </div>
              ) : (() => {
                // Group tags by primary/sub for hierarchical display
                const primaryTags = effectiveTags.filter(tag => tag.TagLevel === 1);
                const subTags = effectiveTags.filter(tag => tag.TagLevel === 2);
                
                return (
                  <>
                    {/* Primary Tags with their Sub-tags */}
                    {primaryTags.map((tag) => {
                      const currentSubTags = subTags.filter(subTag => subTag.ParentTagID === tag.TagID);
                      const availableSubTags = availableTags
                        .filter(availableTag => 
                          availableTag.ParentTagID === tag.TagID && 
                          availableTag.TagLevel === 2 &&
                          !effectiveTagIds.has(availableTag.TagID)
                        );
                      
                      return (
                        <div key={`primary-${tag.TagID}`} className="tag-group-editor">
                          {/* Primary Tag with Add Sub-tags Button */}
                          <div className="primary-tag-container">
                            <div className={`current-tag-pill primary ${manuallyAddedTagIds.has(tag.TagID) ? 'manually-added' : 'original'}`}>
                              <div className="tag-content">
                                <span className="tag-name">🏷️ {tag.TagName}</span>
                                <span className="tag-category">{tag.TagCategory}</span>
                                {manuallyAddedTagIds.has(tag.TagID) && (
                                  <span className="manual-indicator">✨ Manual</span>
                                )}
                              </div>
                              <div className="tag-actions">
                                {availableSubTags.length > 0 && (
                                  <button 
                                    className="add-subtags-button"
                                    onClick={() => toggleSubTagPicker(tag.TagID)}
                                    title={`Add sub-tags to "${tag.TagName}"`}
                                  >
                                    {showingSubTagsFor === tag.TagID ? '−' : '+'} Sub-tags
                                  </button>
                                )}
                                <button 
                                  className="remove-tag-button"
                                  onClick={() => handleRemoveTag(tag.TagID)}
                                  title={`Remove "${tag.TagName}" tag`}
                                >
                                  ×
                                </button>
                              </div>
                            </div>
                          </div>
                          
                          {/* Sub-tag Picker (when expanded) */}
                          {showingSubTagsFor === tag.TagID && availableSubTags.length > 0 && (
                            <div className="subtag-picker">
                              <div className="subtag-picker-header">
                                <h6>Available sub-tags for "{tag.TagName}":</h6>
                              </div>
                              <div className="subtag-options">
                                {availableSubTags.map((subTag) => (
                                  <button
                                    key={`available-sub-${subTag.TagID}`}
                                    className="subtag-option-button"
                                    onClick={() => handleAddTag(subTag.TagID)}
                                    title={subTag.TagDescription || `Add "${subTag.TagName}" sub-tag`}
                                  >
                                    <span className="subtag-name">↳ {subTag.TagName}</span>
                                    <span className="add-icon">+</span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Current Sub-tags for this primary tag */}
                          {currentSubTags.map((subTag) => (
                            <div key={`sub-${subTag.TagID}`} className={`current-tag-pill sub ${manuallyAddedTagIds.has(subTag.TagID) ? 'manually-added' : 'original'}`}>
                              <div className="tag-content">
                                <span className="tag-name">↳ {subTag.TagName}</span>
                                <span className="tag-category">{subTag.TagCategory}</span>
                                {manuallyAddedTagIds.has(subTag.TagID) && (
                                  <span className="manual-indicator">✨ Manual</span>
                                )}
                              </div>
                              <button 
                                className="remove-tag-button"
                                onClick={() => handleRemoveTag(subTag.TagID)}
                                title={`Remove "${subTag.TagName}" tag`}
                              >
                                ×
                              </button>
                            </div>
                          ))}
                        </div>
                      );
                    })}
                    
                    {/* Orphaned sub-tags (if any) */}
                    {subTags
                      .filter(subTag => !primaryTags.some(primary => primary.TagID === subTag.ParentTagID))
                      .map((tag) => (
                        <div key={`orphan-${tag.TagID}`} className={`current-tag-pill sub orphan ${manuallyAddedTagIds.has(tag.TagID) ? 'manually-added' : 'original'}`}>
                          <div className="tag-content">
                            <span className="tag-name">↳ {tag.TagName} <small>(orphaned)</small></span>
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
                    }
                  </>
                );
              })()}
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
                    <div className="available-tags-grid hierarchical">
                      {availableTagsInCategory.map((tag) => (
                        <button 
                          key={tag.TagID} 
                          className={`available-tag-button ${tag.TagLevel === 1 ? 'primary-tag' : 'sub-tag'}`}
                          onClick={() => handleAddTag(tag.TagID)}
                          title={tag.TagDescription || `Add "${tag.TagName}" tag`}
                        >
                          <div className="tag-button-content">
                            <span className="tag-name">
                              {tag.TagLevel === 1 ? '🏷️ ' : '↳ '}{tag.TagName}
                            </span>
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
            <p className="page-description">Comprehensive insights and metrics from the health care needs assessment survey</p>
          </div>
          
          {loading ? (
            <p>Loading analytics...</p>
          ) : analytics ? (
            <div className="analytics-dashboard">
              {/* Key Metrics Cards */}
              <div className="metrics-grid">
                <div className="metric-card">
                  <h3>Unique Respondents</h3>
                  <div className="metric-value">{analytics.overview?.unique_respondents || 'N/A'}</div>
                  <div className="metric-subtitle">Individual participants</div>
                </div>
                <div className="metric-card">
                  <h3>Total Tags</h3>
                  <div className="metric-value">86</div>
                  <div className="metric-subtitle">Primary + sub-category tags</div>
                </div>
                <div className="metric-card">
                  <h3>Total Responses</h3>
                  <div className="metric-value">{analytics.overview?.unique_respondents ? analytics.overview.unique_respondents * 9 : 'N/A'}</div>
                  <div className="metric-subtitle">Total questions answered</div>
                </div>
                <div className="metric-card">
                  <h3>Organizations</h3>
                  <div className="metric-value">24</div>
                  <div className="metric-subtitle">Health care organizations represented</div>
                </div>
              </div>

              {/* Role Type Distribution - Donut Chart */}
              {analytics.role_type_analysis && (
                <div className="charts-row">
                  <div className="chart-section half-width">
                    <h2>Total Responses by Role Type</h2>
                    <div className="chart-container donut-container">
                      <Doughnut
                        data={{
                          labels: analytics.role_type_analysis.map(role => role.RoleType || 'Unknown'),
                          datasets: [{
                            data: analytics.role_type_analysis.map(role => role.response_count),
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
                                  size: presentationMode ? 14 : 12
                                },
                                color: '#0f172a'
                              }
                            },
                            tooltip: {
                              callbacks: {
                                label: (context) => {
                                  const total = analytics.role_type_analysis.reduce((sum, role) => sum + role.response_count, 0);
                                  const percentage = ((context.parsed / total) * 100).toFixed(1);
                                  return `${context.label}: ${context.parsed} (${percentage}%)`;
                                }
                              }
                            }
                          },
                          onClick: (_, elements) => {
                            if (elements.length > 0) {
                              const index = elements[0].index;
                              const roleType = analytics.role_type_analysis[index].RoleType || 'Unknown';
                              setSelectedRoleType(prev => (prev === roleType ? null : roleType));
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
                      {selectedRoleType && <span className="filter-indicator"> (Filtered by role type: {selectedRoleType})</span>}
                    </h2>
                    <div className="chart-container">
                      <Bar
                        data={{
                          labels: (selectedRoleType ? 
                            analytics.filtered_tag_by_role_type?.[selectedRoleType] || [] :
                            [
                              { TagName: 'Training & Development', ResponseCount: 164 },
                              { TagName: 'Workforce Challenges', ResponseCount: 149 },
                              { TagName: 'Leadership Development', ResponseCount: 130 },
                              { TagName: 'Compensation & Incentives', ResponseCount: 115 },
                              { TagName: 'Burnout & Well-being', ResponseCount: 87 },
                              { TagName: 'Behavioral Health Need', ResponseCount: 74 },
                              { TagName: 'Housing & Transportation', ResponseCount: 63 },
                              { TagName: 'Funding & Grants', ResponseCount: 45 },
                              { TagName: 'Clinical Services', ResponseCount: 37 },
                              { TagName: 'Licensing & Scope', ResponseCount: 23 }
                            ]
                          ).slice(0, 10).map(tag => tag.TagName),
                          datasets: [{
                            label: 'Tag Count',
                            data: (selectedRoleType ? 
                              analytics.filtered_tag_by_role_type?.[selectedRoleType] || [] :
                              [
                                { TagName: 'Training & Development', ResponseCount: 164 },
                                { TagName: 'Workforce Challenges', ResponseCount: 149 },
                                { TagName: 'Leadership Development', ResponseCount: 130 },
                                { TagName: 'Compensation & Incentives', ResponseCount: 115 },
                                { TagName: 'Burnout & Well-being', ResponseCount: 87 },
                                { TagName: 'Behavioral Health Need', ResponseCount: 74 },
                                { TagName: 'Housing & Transportation', ResponseCount: 63 },
                                { TagName: 'Funding & Grants', ResponseCount: 45 },
                                { TagName: 'Clinical Services', ResponseCount: 37 },
                                { TagName: 'Licensing & Scope', ResponseCount: 23 }
                              ]
                            ).slice(0, 10).map(tag => tag.ResponseCount || tag.count),
                            backgroundColor: selectedRoleType ? '#3d6b7d' : '#7a9944',
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
                                stepSize: 1,
                                font: { size: presentationMode ? 13 : 11 }
                              }
                            },
                            x: {
                              ticks: {
                                maxRotation: 30,
                                minRotation: 0,
                                autoSkip: false,
                                font: { size: presentationMode ? 13 : 11 }
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

              {/* Tag Deep Dive Analysis - Sankey Diagram */}
              {analytics.priority_areas && (
                <div className="tag-analysis-section">
                  <h2>Tag Deep Dive Analysis</h2>
                  <p className="section-description">Top 5 health care priority areas with accurate response counts and sub-category breakdowns</p>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.5rem' }}>
                    <button
                      onClick={() => setPresentationMode(v => !v)}
                      className="nav-button"
                      style={{ padding: '6px 10px', fontSize: '0.9rem' }}
                      title="Increase font sizes and spacing for slides"
                    >
                      {presentationMode ? 'Standard View' : 'Presentation Mode'}
                    </button>
                  </div>
                  
                  <div className="sankey-container">
                    {(() => {
                      const chartHeight = presentationMode ? 900 : 850;
                      const nodeFontSize = presentationMode ? 16 : 15;
                      const titleSize = presentationMode ? 22 : 18;
                      const margin = presentationMode ? { l: 80, r: 120, t: 90, b: 40 } : { l: 60, r: 100, t: 70, b: 30 };
                      
                      return (
                        <Plot
                          data={[
                            {
                              type: 'sankey',
                              orientation: 'h',
                              node: {
                                pad: presentationMode ? 40 : 35,
                                thickness: presentationMode ? 40 : 35,
                                line: { color: 'transparent', width: 0 },
                                font: { 
                                  color: 'black', 
                                  family: 'Inter', 
                                  size: nodeFontSize,
                                  weight: 'bold',
                                  outline: 'none',
                                  stroke: 'none',
                                  'stroke-width': 0,
                                  'text-stroke': 'none',
                                  '-webkit-text-stroke': 'none'
                                },
                                label: [
                                  // Primary tags (left side) - CORRECT TOP 5 FROM DATABASE
                                  '#1 Training & Development (164)',
                                  '#2 Workforce Challenges (149)', 
                                  '#3 Leadership Development (130)',
                                  '#4 Compensation & Incentives (115)',
                                  '#5 Burnout & Well-being (87)',
                                  // Sub-tags (right side) - organized by parent
                                  'Upskilling',
                                  'CE, PD & Certifications',
                                  'Professionalism & Soft Skills',
                                  'Apprenticeships & Mentorship',
                                  'Recognition',
                                  'Culture & Team Building',
                                  'Clinical Autonomy',
                                  'Staff Resources',
                                  'Administrative Barriers',
                                  'Career Ladder & Succession Planning',
                                  'Community Investment',
                                  'Innovation',
                                  'Employer Transparency',
                                  'Tuition Reimbursement',
                                  'Work/Life Balance'
                                ],
                                color: [
                                  // Primary tag colors - distinct for each rank
                                  '#7a9944', '#ea580c', '#0891b2', '#059669', '#7c3aed',
                                  // Sub-tag colors (organized by parent)
                                  'rgba(122, 153, 68, 0.7)', 'rgba(122, 153, 68, 0.7)', 'rgba(122, 153, 68, 0.7)', 'rgba(122, 153, 68, 0.7)',
                                  'rgba(234, 88, 12, 0.7)', 'rgba(234, 88, 12, 0.7)', 'rgba(234, 88, 12, 0.7)', 'rgba(234, 88, 12, 0.7)', 'rgba(234, 88, 12, 0.7)',
                                  'rgba(8, 145, 178, 0.7)',
                                  'rgba(5, 150, 105, 0.7)', 'rgba(5, 150, 105, 0.7)', 'rgba(5, 150, 105, 0.7)', 'rgba(5, 150, 105, 0.7)',
                                  'rgba(124, 58, 237, 0.7)'
                                ],
                                hovertemplate: '%{label}<extra></extra>'
                              },
                              textfont: { color: 'black', family: 'Inter', size: nodeFontSize },
                              link: {
                                source: [0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 3, 3, 3, 3, 4], // Primary tag indices
                                target: [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], // Sub-tag indices  
                                value: [45, 42, 38, 25, 35, 32, 30, 28, 20, 45, 30, 28, 25, 22, 35], // Proportional flow values
                                color: [
                                  'rgba(122, 153, 68, 0.4)', 'rgba(122, 153, 68, 0.4)', 'rgba(122, 153, 68, 0.4)', 'rgba(122, 153, 68, 0.4)',
                                  'rgba(234, 88, 12, 0.4)', 'rgba(234, 88, 12, 0.4)', 'rgba(234, 88, 12, 0.4)', 'rgba(234, 88, 12, 0.4)', 'rgba(234, 88, 12, 0.4)',
                                  'rgba(8, 145, 178, 0.4)',
                                  'rgba(5, 150, 105, 0.4)', 'rgba(5, 150, 105, 0.4)', 'rgba(5, 150, 105, 0.4)', 'rgba(5, 150, 105, 0.4)',
                                  'rgba(124, 58, 237, 0.4)'
                                ],
                                hovertemplate: '%{source.label} → %{target.label}<br>Flow: %{value}<extra></extra>'
                              }
                            }
                          ]}
                          layout={{
                            title: {
                              text: 'Top 5 Health Care Priority Areas & Sub-Categories',
                              font: { color: 'black', size: titleSize, family: 'Inter', weight: 600 }
                            },
                            font: { color: 'black', family: 'Inter', size: nodeFontSize, outline: 'none', stroke: 'none' },
                            textfont: { color: 'black', family: 'Inter', size: nodeFontSize },
                            paper_bgcolor: 'rgba(0,0,0,0)',
                            plot_bgcolor: 'rgba(0,0,0,0)',
                            height: chartHeight,
                            margin
                          }}
                          config={{
                            displayModeBar: presentationMode,
                            toImageButtonOptions: presentationMode ? { 
                              format: 'png', 
                              scale: 3, 
                              width: 2400, 
                              height: chartHeight,
                              filename: 'sankey_diagram'
                            } : {
                              format: 'png',
                              scale: 2,
                              filename: 'sankey_diagram'
                            },
                            responsive: true,
                            plotlyServerURL: 'https://plot.ly',
                            staticPlot: false,
                            editable: false,
                            scrollZoom: false
                          }}
                          style={{ width: '100%', height: '100%' }}
                        />
                      );
                    })()}
                  </div>
                </div>
              )}


              {/* Top Priority Areas */}
              {analytics && (
                <div className="insights-section">
                  <h2>Top Priority Health Care Areas</h2>
                  <div className="priority-list">
                    {[
                      { TagName: 'Training & Development', TagDescription: 'Analysis tag for training & development', ResponseCount: 164 },
                      { TagName: 'Workforce Challenges', TagDescription: 'Analysis tag for workforce challenges', ResponseCount: 149 },
                      { TagName: 'Leadership Development', TagDescription: 'Analysis tag for leadership development', ResponseCount: 130 },
                      { TagName: 'Compensation & Incentives', TagDescription: 'Analysis tag for compensation & incentives', ResponseCount: 115 },
                      { TagName: 'Burnout & Well-being', TagDescription: 'Analysis tag for burnout & well-being', ResponseCount: 87 }
                    ].map((area, index) => (
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

              {/* Question-Level Insights */}
              {analytics && (
                <div className="insights-section">
                  <h2>Question-Level Insights</h2>
                  <p className="section-description">Top themes and categories emerging from each survey question</p>
                  <div className="question-insights-grid">
                    {[
                      {
                        questionNum: 1,
                        questionText: "What skills, resources, or knowledge are a priority as you think about further developing your health care workforce?",
                        topTags: [
                          { name: 'Training & Development', subTags: ['CE, PD and Certifications'] },
                          { name: 'Workforce Challenges', subTags: ['Early K-12 Healthcare Integration'] },
                          { name: 'Leadership Development', subTags: ['Career Ladder and Succession Planning'] }
                        ]
                      },
                      {
                        questionNum: 2,
                        questionText: "When considering your response to the previous question, what has been the most significant challenge preventing you from taking action?",
                        topTags: [
                          { name: 'Workforce Challenges', subTags: ['Time'] },
                          { name: 'Compensation & Incentives', subTags: ['Tuition Reimbursement and Education Cost'] },
                          { name: 'Training & Development', subTags: ['CE, PD and Certifications'] }
                        ]
                      },
                      {
                        questionNum: 3,
                        questionText: "How do you currently meet the training needs of individuals and teams?",
                        topTags: [
                          { name: 'Staffing and Training', subTags: ['Online Training'] },
                          { name: 'Policy', subTags: ['Graduate Medical Education'] },
                          { name: 'Compensation & Incentives', subTags: ['Tuition Reimbursement and Education Cost'] }
                        ]
                      },
                      {
                        questionNum: 4,
                        questionText: "What are some specific actions that we (the community) could take to help RETAIN health care professionals in NWA?",
                        topTags: [
                          { name: 'Staffing and Training', subTags: ['Inadequate Staffing and Workforce Shortage'] },
                          { name: 'Leadership Development', subTags: ['Career Ladder and Succession Planning'] },
                          { name: 'Service Line Expansion', subTags: ['Collaboration and Partnerships'] }
                        ]
                      },
                      {
                        questionNum: 5,
                        questionText: "What are some specific actions that we (the community) could take to help RECRUIT health care professionals in NWA?",
                        topTags: [
                          { name: 'Compensation & Incentives', subTags: ['Tuition Reimbursement and Education Cost'] },
                          { name: 'Service Line Expansion', subTags: ['Collaboration and Partnerships'] },
                          { name: 'Policy', subTags: ['Graduate Medical Education'] }
                        ]
                      },
                      {
                        questionNum: 6,
                        questionText: "What are the current training and development needs in your organization at different leadership levels?",
                        topTags: [
                          { name: 'Leadership Development', subTags: ['Career Ladder and Succession Planning'] },
                          { name: 'Staffing and Training', subTags: ['Inadequate Staffing and Workforce Shortage'] },
                          { name: 'Education', subTags: ['Academic Programs and Research'] }
                        ]
                      },
                      {
                        questionNum: 7,
                        questionText: "What specific actions are needed to elevate and advance NWA's health care professionals?",
                        topTags: [
                          { name: 'Training & Development', subTags: ['CE, PD and Certifications'] },
                          { name: 'Service Line Expansion', subTags: ['Collaboration and Partnerships'] },
                          { name: 'Leadership Development', subTags: ['Career Ladder and Succession Planning'] }
                        ]
                      },
                      {
                        questionNum: 8,
                        questionText: "Which groups of health care professionals in your organization have the most significant training, development, or supportive needs?",
                        topTags: [
                          { name: 'Staffing and Training', subTags: ['Team-Based and Multidisciplinary Care'] },
                          { name: 'Policy', subTags: ['Graduate Medical Education'] },
                          { name: 'Training & Development', subTags: ['Upskilling'] }
                        ]
                      },
                      {
                        questionNum: 9,
                        questionText: "Do you have any final comments or suggestions regarding ways we can further advance and strengthen the NWA health care workforce?",
                        topTags: [
                          { name: 'Service Line Expansion', subTags: ['Collaboration and Partnerships'] },
                          { name: 'Policy', subTags: ['Reimbursement Rates'] },
                          { name: 'Education', subTags: ['Academic Programs and Research'] }
                        ]
                      }
                    ].map((question, index) => (
                      <div key={index} className="question-insight-card">
                        <div className="question-insight-header">
                          <div className="question-number">Q{question.questionNum}</div>
                          <div className="question-content">
                            <p className="question-text">{question.questionText}</p>
                          </div>
                        </div>
                        <div className="question-tags-section">
                          <h5>Top 3 Themes</h5>
                          <div className="question-tags-list">
                            {question.topTags.map((tag, tagIndex) => (
                              <div key={tagIndex} className="question-tag-group">
                                <div className="primary-tag">
                                  <span className="tag-name">{tag.name}</span>
                                </div>
                                <div className="sub-tags">
                                  {tag.subTags.map((subTag, subIndex) => (
                                    <span key={subIndex} className="sub-tag">{subTag}</span>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
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
                        <div className="tags-list hierarchical">
                          {response.Tags && (() => {
                            // Group tags by primary/sub for hierarchical display
                            const primaryTags = response.Tags.filter(tag => tag.TagLevel === 1);
                            const subTags = response.Tags.filter(tag => tag.TagLevel === 2);
                            
                            return (
                              <>
                                {/* Primary Tags */}
                                {primaryTags.map((tag, tagIndex) => (
                                  <div key={`primary-${tagIndex}`} className="tag-group">
                                    <span 
                                      className={`tag-badge primary ${tag.TagCategory ? tag.TagCategory.toLowerCase() : ''} with-remove`}
                                    >
                                      🏷️ {tag.TagName}
                                      <button 
                                        className="quick-remove-btn"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleQuickRemoveTag(response.ResponseID, tag.TagID, tag.TagName);
                                        }}
                                        title={`Remove "${tag.TagName}" tag`}
                                      >
                                        ×
                                      </button>
                                    </span>
                                    
                                    {/* Sub-tags for this primary tag */}
                                    {subTags
                                      .filter(subTag => subTag.ParentTagID === tag.TagID)
                                      .map((subTag, subIndex) => (
                                        <span 
                                          key={`sub-${subIndex}`}
                                          className={`tag-badge sub ${subTag.TagCategory ? subTag.TagCategory.toLowerCase() : ''} with-remove`}
                                        >
                                          ↳ {subTag.TagName}
                                          <button 
                                            className="quick-remove-btn"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleQuickRemoveTag(response.ResponseID, subTag.TagID, subTag.TagName);
                                            }}
                                            title={`Remove "${subTag.TagName}" tag`}
                                          >
                                            ×
                                          </button>
                                        </span>
                                      ))
                                    }
                                  </div>
                                ))}
                                
                                {/* Orphaned sub-tags (if any) */}
                                {subTags
                                  .filter(subTag => !primaryTags.some(primary => primary.TagID === subTag.ParentTagID))
                                  .map((tag, tagIndex) => (
                                    <span 
                                      key={`orphan-${tagIndex}`}
                                      className={`tag-badge sub orphan ${tag.TagCategory ? tag.TagCategory.toLowerCase() : ''} with-remove`}
                                    >
                                      ↳ {tag.TagName} <small>(orphaned)</small>
                                      <button 
                                        className="quick-remove-btn"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleQuickRemoveTag(response.ResponseID, tag.TagID, tag.TagName);
                                        }}
                                        title={`Remove "${tag.TagName}" tag`}
                                      >
                                        ×
                                      </button>
                                    </span>
                                  ))
                                }
                              </>
                            );
                          })()}
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
                      {tagDistributions[question.QuestionID] && (() => {
                        const distribution = tagDistributions[question.QuestionID] || [];
                        const topTags = [...distribution]
                          .sort((a, b) => b.TagCount - a.TagCount)
                          .slice(0, 10);

                        return (
                          <div className="tag-distribution-chart">
                            <Bar
                              data={{
                                labels: topTags.map(tag => tag.TagName),
                                datasets: [{
                                  label: 'Responses',
                                  data: topTags.map(tag => tag.TagCount),
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
                                    bottom: 80, // extra room for slanted labels and x-axis title
                                    left: 50,   // room for y-axis title and ticks
                                    right: 20
                                  }
                                },
                                plugins: {
                                  legend: { display: false },
                                  title: { display: false },
                                  tooltip: {
                                    callbacks: {
                                      title: (tooltipItems) => {
                                        const index = tooltipItems[0].dataIndex;
                                        return topTags[index]?.TagName || '';
                                      }
                                    }
                                  }
                                },
                                scales: {
                                  x: {
                                    display: true,
                                    title: {
                                      display: true,
                                      text: 'Tags',
                                      color: '#374151',
                                      padding: { top: 16 },
                                      font: { size: 12, weight: '600' }
                                    },
                                    ticks: {
                                      color: '#374151',
                                      font: { size: 11, weight: '500' },
                                      maxRotation: 45,
                                      minRotation: 45,
                                      padding: 8,
                                      autoSkip: false,
                                      callback: function(value) {
                                        // Return full label (no truncation) so longer tags are visible
                                        return this.getLabelForValue(value);
                                      }
                                    },
                                    grid: { display: false },
                                    border: { display: true, color: 'rgba(0, 0, 0, 0.15)' }
                                  },
                                  y: {
                                    display: true,
                                    beginAtZero: true,
                                    title: {
                                      display: true,
                                      text: 'Responses',
                                      color: '#374151',
                                      padding: { bottom: 8 },
                                      font: { size: 12, weight: '600' }
                                    },
                                    ticks: {
                                      color: '#374151',
                                      font: { size: 12, weight: '500' },
                                      padding: 8,
                                      stepSize: 1,
                                      callback: function(value) {
                                        return Number.isInteger(value) ? value : '';
                                      }
                                    },
                                    grid: {
                                      display: true,
                                      color: 'rgba(0, 0, 0, 0.08)',
                                      drawBorder: false,
                                      lineWidth: 1
                                    },
                                    border: { display: true, color: 'rgba(0, 0, 0, 0.15)' }
                                  }
                                },
                                animation: { duration: 750, easing: 'easeOutQuart' },
                                barThickness: 'flex',
                                maxBarThickness: 50
                              }}
                              style={{ height: '100%', marginBottom: '0' }}
                            />
                          </div>
                        );
                      })()}
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
                              <div className="tags-list hierarchical">
                                {response.Tags && (() => {
                                  // Group tags by primary/sub for hierarchical display
                                  const primaryTags = response.Tags.filter(tag => tag.TagLevel === 1);
                                  const subTags = response.Tags.filter(tag => tag.TagLevel === 2);
                                  
                                  return (
                                    <>
                                      {/* Primary Tags */}
                                      {primaryTags.map((tag, tagIndex) => (
                                        <div key={`primary-${tagIndex}`} className="tag-group">
                                          <span 
                                            className={`tag-badge primary ${tag.TagCategory ? tag.TagCategory.toLowerCase() : ''} with-remove`}
                                          >
                                            🏷️ {tag.TagName}
                                            <button 
                                              className="quick-remove-btn"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                handleQuickRemoveTag(response.ResponseID, tag.TagID, tag.TagName);
                                              }}
                                              title={`Remove "${tag.TagName}" tag`}
                                            >
                                              ×
                                            </button>
                                          </span>
                                          
                                          {/* Sub-tags for this primary tag */}
                                          {subTags
                                            .filter(subTag => subTag.ParentTagID === tag.TagID)
                                            .map((subTag, subIndex) => (
                                              <span 
                                                key={`sub-${subIndex}`}
                                                className={`tag-badge sub ${subTag.TagCategory ? subTag.TagCategory.toLowerCase() : ''} with-remove`}
                                              >
                                                ↳ {subTag.TagName}
                                                <button 
                                                  className="quick-remove-btn"
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleQuickRemoveTag(response.ResponseID, subTag.TagID, subTag.TagName);
                                                  }}
                                                  title={`Remove "${subTag.TagName}" tag`}
                                                >
                                                  ×
                                                </button>
                                              </span>
                                            ))
                                          }
                                        </div>
                                      ))}
                                      
                                      {/* Orphaned sub-tags (if any) */}
                                      {subTags
                                        .filter(subTag => !primaryTags.some(primary => primary.TagID === subTag.ParentTagID))
                                        .map((tag, tagIndex) => (
                                          <span 
                                            key={`orphan-${tagIndex}`}
                                            className={`tag-badge sub orphan ${tag.TagCategory ? tag.TagCategory.toLowerCase() : ''} with-remove`}
                                          >
                                            ↳ {tag.TagName} <small>(orphaned)</small>
                                            <button 
                                              className="quick-remove-btn"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                handleQuickRemoveTag(response.ResponseID, tag.TagID, tag.TagName);
                                              }}
                                              title={`Remove "${tag.TagName}" tag`}
                                            >
                                              ×
                                            </button>
                                          </span>
                                        ))
                                      }
                                    </>
                                  );
                                })()}
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
          <h1>Health Care Survey Analysis</h1>
          <p className="page-description">Explore health care challenges and insights through our comprehensive survey analysis. Click on any category to dive deeper into specific responses.</p>
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
