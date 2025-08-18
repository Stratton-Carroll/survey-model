"""
Organization Dimension Table Creation
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config import DEFAULT_ORGANIZATION, ORGANIZATION_COLUMN

def classify_organization_type(org_name):
    """Classify organization based on name patterns"""
    org_lower = str(org_name).lower()
    
    if any(word in org_lower for word in ['hospital', 'medical center', 'regional']):
        return 'Hospital'
    elif any(word in org_lower for word in ['clinic', 'family medicine', 'primary care']):
        return 'Clinic'
    elif any(word in org_lower for word in ['university', 'college', 'uams', 'academic']):
        return 'Academic'
    elif any(word in org_lower for word in ['county', 'state', 'department', 'public health']):
        return 'Government'
    else:
        return 'Other'

def estimate_organization_size(org_name):
    """Estimate organization size based on type and name"""
    org_lower = str(org_name).lower()
    
    if any(word in org_lower for word in ['regional', 'system', 'university', 'medical center']):
        return 'Large (500+ employees)'
    elif any(word in org_lower for word in ['hospital', 'clinic', 'group']):
        return 'Medium (100-500 employees)'
    else:
        return 'Small (<100 employees)'

def create_organization_dimension(df):
    """Create the organization dimension table"""
    
    # Use the structured organization column
    if ORGANIZATION_COLUMN not in df.columns:
        print(f"⚠️ Warning: {ORGANIZATION_COLUMN} column not found")
        return pd.DataFrame()
    
    # Get unique organizations
    organizations = df[ORGANIZATION_COLUMN].dropna().unique()
    
    dim_organization = []
    org_id = 1
    
    for org in organizations:
        org_clean = str(org).strip()
        org_type = classify_organization_type(org_clean)
        org_size = estimate_organization_size(org_clean)
        
        dim_organization.append({
            'OrganizationID': org_id,
            'OrganizationName': org_clean,
            'OrganizationType': org_type,
            'OrganizationSize': org_size,
            'IsHealthSystem': 1 if 'system' in org_clean.lower() else 0,
            'IsAcademic': 1 if org_type == 'Academic' else 0,
            'IsGovernment': 1 if org_type == 'Government' else 0
        })
        org_id += 1
    
    # Add default "Unknown" organization
    dim_organization.append({
        'OrganizationID': org_id,
        'OrganizationName': DEFAULT_ORGANIZATION,
        'OrganizationType': 'Unknown',
        'OrganizationSize': 'Unknown',
        'IsHealthSystem': 0,
        'IsAcademic': 0,
        'IsGovernment': 0
    })
    
    df_result = pd.DataFrame(dim_organization)
    print(f"🏢 Created DimOrganization with {len(df_result)} organizations")
    
    return df_result

if __name__ == "__main__":
    # Test the dimension creation
    from data_loader import load_survey_data
    df = load_survey_data()
    if df is not None:
        dim_df = create_organization_dimension(df)
        print(dim_df.head())
