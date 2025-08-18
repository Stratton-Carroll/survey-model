import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('tags'); // 'tags', 'tag-detail', 'responses'
  const [tags, setTags] = useState([]);
  const [selectedTag, setSelectedTag] = useState(null);
  const [responses, setResponses] = useState([]);
  const [questionsWithResponses, setQuestionsWithResponses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedQuestions, setExpandedQuestions] = useState(new Set());

  useEffect(() => {
    if (currentView === 'tags') {
      fetch('http://127.0.0.1:5000/api/tags')
        .then(response => response.json())
        .then(data => setTags(data))
        .catch(error => console.error('Error fetching tags:', error));
    } else if (currentView === 'responses') {
      setLoading(true);
      fetch('http://127.0.0.1:5000/api/responses')
        .then(response => response.json())
        .then(data => setQuestionsWithResponses(data))
        .catch(error => console.error('Error fetching responses:', error))
        .finally(() => setLoading(false));
    }
  }, [currentView]);

  const handleTagClick = async (tag) => {
    setSelectedTag(tag);
    setCurrentView('tag-detail');
    setLoading(true);
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/tags/${tag.TagID}/responses`);
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

  const toggleQuestion = (questionId) => {
    const newExpanded = new Set(expandedQuestions);
    if (newExpanded.has(questionId)) {
      newExpanded.delete(questionId);
    } else {
      newExpanded.add(questionId);
    }
    setExpandedQuestions(newExpanded);
  };

  // Tag detail view
  if (currentView === 'tag-detail' && selectedTag) {
    return (
      <div className="App">
        <header className="App-header">
          <div className="nav-buttons">
            <button onClick={handleBackClick} className="back-button">← Back to Tags</button>
            <button onClick={handleViewResponses} className="nav-button">View All Responses</button>
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
                        <span className="role">{response.RoleName}</span>
                        <span className="location">{response.PrimaryCounty}, {response.State}</span>
                        {response.OrganizationType && (
                          <span className="org-type">{response.OrganizationType}</span>
                        )}
                      </div>
                    </div>
                    
                    <div className="response-content">
                      <p className="response-text">{response.ResponseText}</p>
                    </div>
                    
                    {response.OrganizationName && (
                      <div className="response-footer">
                        <span className="org-info">Organization: {response.OrganizationName}</span>
                      </div>
                    )}
                    
                    {response.Tags && response.Tags.length > 0 && (
                      <div className="response-tags">
                        <span className="tags-label">All Tags:</span>
                        <div className="tags-list">
                          {response.Tags.map((tag, tagIndex) => (
                            <span 
                              key={tagIndex} 
                              className={`tag-badge ${tag.TagCategory?.toLowerCase()} ${
                                tag.TagID === selectedTag.TagID ? 'primary-tag' : ''
                              }`}
                              onClick={() => {
                                const tagObj = tags.find(t => t.TagID == tag.TagID);
                                if (tagObj && tag.TagID !== selectedTag.TagID) {
                                  handleTagClick(tagObj);
                                }
                              }}
                            >
                              {tag.TagName}
                              {tag.TagID === selectedTag.TagID && ' ★'}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </header>
      </div>
    );
  }

  // Responses by question view
  if (currentView === 'responses') {
    return (
      <div className="App">
        <header className="App-header">
          <div className="nav-buttons">
            <button onClick={handleViewTags} className="nav-button">← Back to Tags</button>
          </div>
          <h1>Survey Responses by Question</h1>
          <p className="subtitle">Full responses with associated tags</p>
          
          {loading ? (
            <p>Loading responses...</p>
          ) : (
            <div className="questions-container">
              {questionsWithResponses.map(question => (
                <div key={question.QuestionID} className="question-section">
                  <div 
                    className="question-header clickable"
                    onClick={() => toggleQuestion(question.QuestionID)}
                  >
                    <div className="question-header-content">
                      <h2>{question.QuestionShort}</h2>
                      <p className="question-full">{question.QuestionText}</p>
                      <span className="response-count">{question.responses.length} responses</span>
                    </div>
                    <div className="expand-icon">
                      {expandedQuestions.has(question.QuestionID) ? '−' : '+'}
                    </div>
                  </div>
                  
                  {expandedQuestions.has(question.QuestionID) && (
                    <div className="question-responses">
                      {question.responses.map((response, index) => (
                        <div key={response.ResponseID} className="full-response-card">
                          <div className="response-header">
                            <div className="response-meta">
                              <span className="role">{response.RoleName}</span>
                              <span className="location">{response.PrimaryCounty}, {response.State}</span>
                              {response.OrganizationType && (
                                <span className="org-type">{response.OrganizationType}</span>
                              )}
                            </div>
                          </div>
                          
                          <div className="response-content">
                            <p className="response-text">{response.ResponseText}</p>
                          </div>
                          
                          {response.OrganizationName && (
                            <div className="response-footer">
                              <span className="org-info">Organization: {response.OrganizationName}</span>
                            </div>
                          )}
                          
                          {response.Tags && response.Tags.length > 0 && (
                            <div className="response-tags">
                              <span className="tags-label">Tags:</span>
                              <div className="tags-list">
                                {response.Tags.map((tag, tagIndex) => (
                                  <span 
                                    key={tagIndex} 
                                    className={`tag-badge ${tag.TagCategory?.toLowerCase()}`}
                                    onClick={() => {
                                      const tagObj = tags.find(t => t.TagID == tag.TagID);
                                      if (tagObj) handleTagClick(tagObj);
                                    }}
                                  >
                                    {tag.TagName}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </header>
      </div>
    );
  }

  // Default tags view
  return (
    <div className="App">
      <header className="App-header">
        <div className="nav-buttons">
          <button onClick={handleViewResponses} className="nav-button">View All Responses</button>
        </div>
        <h1>Healthcare Survey Analysis</h1>
        <p className="subtitle">Click on any tag to see related responses</p>
        <div className="tags-grid">
          {tags.map(tag => (
            <div 
              key={tag.TagID} 
              className="tag-card"
              onClick={() => handleTagClick(tag)}
            >
              <h3>{tag.TagName}</h3>
              <div className="tag-meta">
                <span className="category">{tag.TagCategory}</span>
                <span className="count">{tag.ResponseCount} responses</span>
              </div>
              {tag.TagDescription && (
                <p className="description">{tag.TagDescription}</p>
              )}
            </div>
          ))}
        </div>
      </header>
    </div>
  );
}

export default App;