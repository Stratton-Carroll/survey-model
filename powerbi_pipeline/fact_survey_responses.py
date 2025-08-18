"""
Fact Survey Responses Table Creation
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config import (ORGANIZATION_COLUMN, PRIMARY_COUNTY_COLUMN, ROLE_STANDARDIZED_COLUMN,
                   DEFAULT_ORGANIZATION, DEFAULT_GEOGRAPHY)

def create_fact_table(df, dim_geography, dim_organization, dim_urgency, dim_question, dim_role):
    """Create the main fact table linking all survey responses to dimensions"""
    
    fact_responses = []
    response_id = 1
    
    # Get all question columns (excluding structured data columns)
    structured_columns = [
        'Start time', 'Completion time', 'Organization', 'Organization County', 
        'Primary_County', 'Service_Area', 'Multi_County_Flag', 'Role/Position', 
        'Length of time in current position', 'Role_Standardized', 'Role_Category', 
        'Role_Level', 'Role_Type', 'Time_Range_Category', 'Contact Email'
    ]
    
    question_columns = [col for col in df.columns if col not in structured_columns]
    
    for idx, row in df.iterrows():
        # Get foreign keys
        org_id = get_organization_id(row, dim_organization)
        geo_id = get_geography_id(row, dim_geography)
        role_id = get_role_id(row, dim_role)
        
        # Create a fact record for each question response
        for question_col in question_columns:
            response_text = str(row[question_col]) if pd.notna(row[question_col]) else ''
            
            # Get question ID
            question_id = get_question_id(question_col, dim_question)
            
            # Calculate response metrics
            has_response = 1 if response_text and response_text.strip() and response_text.lower() not in ['nan', ''] else 0
            response_length = len(response_text) if has_response else 0
            word_count = len(response_text.split()) if has_response else 0
            
            # Determine urgency (simplified)
            urgency_id = 1  # Default to first urgency level
            
            fact_responses.append({
                'ResponseID': response_id,
                'SurveyResponseNumber': idx + 1,  # Row number in original survey
                'OrganizationID': org_id,
                'GeographyID': geo_id,
                'RoleID': role_id,
                'QuestionID': question_id,
                'UrgencyID': urgency_id,
                'ResponseText': response_text if has_response else '',  # Full response text
                'ResponseLength': response_length,
                'WordCount': word_count,
                'HasResponse': has_response,
                'IsTextResponse': 1 if response_length > 20 else 0,
                'IsLongResponse': 1 if response_length > 200 else 0
            })
            response_id += 1
    
    df_result = pd.DataFrame(fact_responses)
    print(f"📋 Created FactSurveyResponses with {len(df_result)} records")
    print(f"   📊 Covering {len(df)} survey responses across {len(question_columns)} questions")
    
    return df_result

def get_organization_id(row, dim_organization):
    """Get organization ID from dimension table"""
    if ORGANIZATION_COLUMN in row and pd.notna(row[ORGANIZATION_COLUMN]):
        org_name = str(row[ORGANIZATION_COLUMN]).strip()
        matches = dim_organization[dim_organization['OrganizationName'] == org_name]
        if len(matches) > 0:
            return matches.iloc[0]['OrganizationID']
    
    # Return default (Unknown) organization ID
    unknown_matches = dim_organization[dim_organization['OrganizationName'] == DEFAULT_ORGANIZATION]
    return unknown_matches.iloc[0]['OrganizationID'] if len(unknown_matches) > 0 else 1

def get_geography_id(row, dim_geography):
    """Get geography ID from dimension table"""
    if PRIMARY_COUNTY_COLUMN in row and pd.notna(row[PRIMARY_COUNTY_COLUMN]):
        primary_county = str(row[PRIMARY_COUNTY_COLUMN]).strip()
        # Remove 'County' suffix for matching
        primary_county = primary_county.replace(' County', '').replace('County', '')
        matches = dim_geography[dim_geography['PrimaryCounty'] == primary_county]
        if len(matches) > 0:
            return matches.iloc[0]['GeographyID']
    
    # Return default (Unknown) geography ID
    unknown_matches = dim_geography[dim_geography['PrimaryCounty'] == DEFAULT_GEOGRAPHY]
    return unknown_matches.iloc[0]['GeographyID'] if len(unknown_matches) > 0 else 1

def get_role_id(row, dim_role):
    """Get role ID from dimension table"""
    if ROLE_STANDARDIZED_COLUMN in row and pd.notna(row[ROLE_STANDARDIZED_COLUMN]):
        role_standardized = str(row[ROLE_STANDARDIZED_COLUMN]).strip()
        matches = dim_role[dim_role['RoleStandardized'] == role_standardized]
        if len(matches) > 0:
            return matches.iloc[0]['RoleID']
    
    # Return default (Unknown) role ID
    unknown_matches = dim_role[dim_role['RoleStandardized'] == 'Unknown']
    return unknown_matches.iloc[0]['RoleID'] if len(unknown_matches) > 0 else 1

def get_question_id(question_text, dim_question):
    """Get question ID from dimension table"""
    matches = dim_question[dim_question['QuestionText'] == question_text]
    if len(matches) > 0:
        return matches.iloc[0]['QuestionID']
    return 1  # Default to first question if not found

if __name__ == "__main__":
    # Test with minimal data
    print("Testing fact table creation...")
    test_data = [{'categories': ['training'], 'urgency_level': 'high', 'healthcare_roles': ['nursing'], 
                 'response_length': 100, 'word_count': 20, 'priority_score': 3.5}]
    
    # Create minimal dimensions for testing
    dim_urgency = pd.DataFrame([{'UrgencyID': 1, 'UrgencyKey': 'high'}])
    
    fact_df = create_fact_table(test_data, None, None, None, dim_urgency, None)
    print(fact_df.head())
