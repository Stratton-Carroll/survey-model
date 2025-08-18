"""
Geography Dimension Table Creation
"""

import pandas as pd
import re
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config import DEFAULT_GEOGRAPHY, PRIMARY_COUNTY_COLUMN, ORGANIZATION_COUNTY_COLUMN, SERVICE_AREA_COLUMN, MULTI_COUNTY_FLAG_COLUMN
from healthcare_taxonomy import NWA_REGIONS

def create_geography_dimension(df):
    """Create the geography dimension table"""
    
    # Use the new structured geography columns
    if PRIMARY_COUNTY_COLUMN not in df.columns:
        print(f"⚠️ Warning: {PRIMARY_COUNTY_COLUMN} column not found")
        return pd.DataFrame()
    
    # Get unique combinations of geographic information
    geo_data = df[[PRIMARY_COUNTY_COLUMN, ORGANIZATION_COUNTY_COLUMN, SERVICE_AREA_COLUMN, MULTI_COUNTY_FLAG_COLUMN]].drop_duplicates()
    
    dim_geography = []
    geo_id = 1
    
    for _, row in geo_data.iterrows():
        primary_county = str(row[PRIMARY_COUNTY_COLUMN]) if pd.notna(row[PRIMARY_COUNTY_COLUMN]) else ''
        org_county = str(row[ORGANIZATION_COUNTY_COLUMN]) if pd.notna(row[ORGANIZATION_COUNTY_COLUMN]) else ''
        service_area = str(row[SERVICE_AREA_COLUMN]) if pd.notna(row[SERVICE_AREA_COLUMN]) else ''
        multi_county_flag = str(row[MULTI_COUNTY_FLAG_COLUMN]) if pd.notna(row[MULTI_COUNTY_FLAG_COLUMN]) else 'FALSE'
        
        # Clean primary county name
        primary_county_clean = primary_county.strip()
        
        # Remove 'County' suffix if present
        primary_county_clean = re.sub(r'\s+County\s*$', '', primary_county_clean, flags=re.IGNORECASE)
        
        # Map to region using primary county
        region = NWA_REGIONS.get(primary_county_clean, 'Other Arkansas')
        
        # Determine county type
        is_multi_county = multi_county_flag.upper() == 'TRUE'
        county_type = 'Multi-County' if is_multi_county else 'Single-County'
        
        dim_geography.append({
            'GeographyID': geo_id,
            'PrimaryCounty': primary_county_clean,
            'OrganizationCounty': org_county,
            'ServiceArea': service_area,
            'Region': region,
            'State': 'Arkansas',
            'IsNWA': 1 if region == 'Northwest Arkansas' else 0,
            'IsMultiCounty': 1 if is_multi_county else 0,
            'CountyType': county_type
        })
        geo_id += 1
    
    # Add default "Unknown" geography
    dim_geography.append({
        'GeographyID': geo_id,
        'PrimaryCounty': DEFAULT_GEOGRAPHY,
        'OrganizationCounty': DEFAULT_GEOGRAPHY,
        'ServiceArea': DEFAULT_GEOGRAPHY,
        'Region': 'Unknown',
        'State': 'Unknown',
        'IsNWA': 0,
        'IsMultiCounty': 0,
        'CountyType': 'Unknown'
    })
    
    df_result = pd.DataFrame(dim_geography)
    print(f"📍 Created DimGeography with {len(df_result)} geographic entities")
    
    return df_result

if __name__ == "__main__":
    # Test the dimension creation
    from data_loader import load_survey_data
    df = load_survey_data()
    if df is not None:
        dim_df = create_geography_dimension(df)
        print(dim_df.head())
