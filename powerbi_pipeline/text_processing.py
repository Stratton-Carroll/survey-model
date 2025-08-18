"""
Text processing and tagging functions
Handles categorization, urgency detection, and role extraction
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from healthcare_taxonomy import HEALTHCARE_CATEGORIES, HEALTHCARE_ROLES, URGENCY_INDICATORS
from config import DEFAULT_URGENCY

def categorize_text(text):
    """Categorize text based on healthcare domain keywords"""
    if pd.isna(text):
        return []
    
    text_lower = str(text).lower()
    found_categories = []
    
    for category, info in HEALTHCARE_CATEGORIES.items():
        for keyword in info['keywords']:
            if keyword in text_lower:
                found_categories.append(category)
                break
    
    return found_categories

def extract_urgency(text):
    """Extract urgency level from text"""
    if pd.isna(text):
        return DEFAULT_URGENCY
    
    text_lower = str(text).lower()
    
    # Check for urgency indicators in order of priority (high, low, medium)
    for level in ['high', 'low', 'medium']:
        for indicator in URGENCY_INDICATORS[level]['keywords']:
            if indicator in text_lower:
                return level
    
    return DEFAULT_URGENCY

def extract_healthcare_roles(text):
    """Extract healthcare roles mentioned in text"""
    if pd.isna(text):
        return []
    
    text_lower = str(text).lower()
    found_roles = []
    
    for role_category, role_info in HEALTHCARE_ROLES.items():
        for keyword in role_info['keywords']:
            if keyword in text_lower:
                found_roles.append(role_category)
                break
    
    return found_roles

def calculate_priority_score(categories, urgency_level):
    """Calculate priority score based on categories and urgency"""
    if not categories:
        return 0.0
    
    # Get category weights
    category_weights = []
    for category in categories:
        if category in HEALTHCARE_CATEGORIES:
            category_weights.append(HEALTHCARE_CATEGORIES[category]['priority_weight'])
    
    if not category_weights:
        return 0.0
    
    # Get urgency score
    urgency_score = URGENCY_INDICATORS.get(urgency_level, {'score': 2})['score']
    
    # Calculate weighted priority
    avg_weight = sum(category_weights) / len(category_weights)
    priority_score = avg_weight * urgency_score * len(categories)
    
    return round(priority_score, 2)

def process_response_text(text):
    """Process a single response text and extract all information"""
    if pd.isna(text):
        return {
            'categories': [],
            'urgency_level': DEFAULT_URGENCY,
            'healthcare_roles': [],
            'response_length': 0,
            'word_count': 0,
            'priority_score': 0.0
        }
    
    text_str = str(text)
    categories = categorize_text(text_str)
    urgency_level = extract_urgency(text_str)
    healthcare_roles = extract_healthcare_roles(text_str)
    
    return {
        'categories': categories,
        'urgency_level': urgency_level,
        'healthcare_roles': healthcare_roles,
        'response_length': len(text_str),
        'word_count': len(text_str.split()),
        'priority_score': calculate_priority_score(categories, urgency_level)
    }

def batch_process_responses(df, columns):
    """Process multiple response columns efficiently"""
    processed_data = []
    
    for idx, row in df.iterrows():
        for col in columns:
            if pd.notna(row[col]):
                response_data = process_response_text(row[col])
                response_data.update({
                    'response_id': f"{idx}_{col}",
                    'original_response_id': idx,
                    'question_column': col,
                    'response_text': str(row[col])[:500]  # Truncated
                })
                processed_data.append(response_data)
    
    return processed_data

if __name__ == "__main__":
    # Test the text processing functions
    test_text = "We need urgent training for our nursing staff in clinical skills and leadership development"
    
    result = process_response_text(test_text)
    print("🔧 Text Processing Test:")
    print(f"   Text: {test_text}")
    print(f"   Categories: {result['categories']}")
    print(f"   Urgency: {result['urgency_level']}")
    print(f"   Roles: {result['healthcare_roles']}")
    print(f"   Priority Score: {result['priority_score']}")
    print("✅ Text processing test completed successfully!")
