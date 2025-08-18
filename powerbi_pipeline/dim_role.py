"""
Role Dimension Table Creation
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config import (ROLE_POSITION_COLUMN, ROLE_STANDARDIZED_COLUMN, ROLE_CATEGORY_COLUMN, 
                   ROLE_LEVEL_COLUMN, ROLE_TYPE_COLUMN, TIME_IN_POSITION_COLUMN, 
                   TIME_RANGE_CATEGORY_COLUMN)

def create_role_dimension(df):
    """Create the role dimension table"""
    
    # Check if role columns exist
    required_cols = [ROLE_STANDARDIZED_COLUMN, ROLE_CATEGORY_COLUMN, ROLE_LEVEL_COLUMN, ROLE_TYPE_COLUMN]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"⚠️ Warning: Missing role columns: {missing_cols}")
        return pd.DataFrame()
    
    # Get unique role combinations
    role_cols = [ROLE_POSITION_COLUMN, ROLE_STANDARDIZED_COLUMN, ROLE_CATEGORY_COLUMN, 
                ROLE_LEVEL_COLUMN, ROLE_TYPE_COLUMN, TIME_RANGE_CATEGORY_COLUMN]
    
    available_cols = [col for col in role_cols if col in df.columns]
    role_data = df[available_cols].drop_duplicates()
    
    dim_role = []
    role_id = 1
    
    for _, row in role_data.iterrows():
        role_position = str(row[ROLE_POSITION_COLUMN]) if ROLE_POSITION_COLUMN in row and pd.notna(row[ROLE_POSITION_COLUMN]) else ''
        role_standardized = str(row[ROLE_STANDARDIZED_COLUMN]) if pd.notna(row[ROLE_STANDARDIZED_COLUMN]) else ''
        role_category = str(row[ROLE_CATEGORY_COLUMN]) if pd.notna(row[ROLE_CATEGORY_COLUMN]) else ''
        role_level = str(row[ROLE_LEVEL_COLUMN]) if pd.notna(row[ROLE_LEVEL_COLUMN]) else ''
        role_type = str(row[ROLE_TYPE_COLUMN]) if pd.notna(row[ROLE_TYPE_COLUMN]) else ''
        time_range = str(row[TIME_RANGE_CATEGORY_COLUMN]) if TIME_RANGE_CATEGORY_COLUMN in row and pd.notna(row[TIME_RANGE_CATEGORY_COLUMN]) else ''
        
        # Classify role seniority
        seniority = classify_role_seniority(role_level, role_category)
        
        # Determine if clinical role
        is_clinical = 1 if 'clinical' in role_type.lower() else 0
        is_leadership = 1 if any(word in role_level.lower() for word in ['executive', 'senior', 'director', 'manager', 'leader']) else 0
        is_trainee = 1 if 'trainee' in role_level.lower() or 'resident' in role_standardized.lower() else 0
        
        dim_role.append({
            'RoleID': role_id,
            'RolePosition': role_position,
            'RoleStandardized': role_standardized,
            'RoleCategory': role_category,
            'RoleLevel': role_level,
            'RoleType': role_type,
            'TimeRangeCategory': time_range,
            'RoleSeniority': seniority,
            'IsClinical': is_clinical,
            'IsLeadership': is_leadership,
            'IsTrainee': is_trainee
        })
        role_id += 1
    
    # Add default "Unknown" role
    dim_role.append({
        'RoleID': role_id,
        'RolePosition': 'Unknown',
        'RoleStandardized': 'Unknown',
        'RoleCategory': 'Unknown',
        'RoleLevel': 'Unknown',
        'RoleType': 'Unknown',
        'TimeRangeCategory': 'Unknown',
        'RoleSeniority': 'Unknown',
        'IsClinical': 0,
        'IsLeadership': 0,
        'IsTrainee': 0
    })
    
    df_result = pd.DataFrame(dim_role)
    print(f"👥 Created DimRole with {len(df_result)} role configurations")
    
    return df_result

def classify_role_seniority(role_level, role_category):
    """Classify role seniority based on level and category"""
    level_lower = str(role_level).lower()
    category_lower = str(role_category).lower()
    
    if 'c-suite' in level_lower or 'executive' in level_lower:
        return 'Executive'
    elif 'senior' in level_lower or 'director' in level_lower:
        return 'Senior Leadership'
    elif 'management' in level_lower or 'manager' in level_lower:
        return 'Management'
    elif 'professional' in level_lower:
        return 'Professional'
    elif 'trainee' in level_lower:
        return 'Trainee'
    else:
        return 'Other'

if __name__ == "__main__":
    # Test the dimension creation
    from data_loader import load_survey_data
    df = load_survey_data()
    if df is not None:
        dim_df = create_role_dimension(df)
        print(dim_df.head())
