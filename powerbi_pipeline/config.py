"""
Configuration file for Power BI Data Model Pipeline
Contains all constants and settings
"""

import os

# File paths
DATA_FILE = '../data/Need_Assessment_Survey_FINAL_CLEAN.csv'
OUTPUT_DIR = '../powerbi_data_model_v2'
PIPELINE_DIR = 'powerbi_pipeline'

# Ensure output directory exists
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Data processing settings
MAX_RESPONSE_TEXT_LENGTH = 500  # Truncate long responses
DEFAULT_URGENCY = 'medium'
DEFAULT_ORGANIZATION = 'Unknown'
DEFAULT_GEOGRAPHY = 'Unknown'

# Column names for the new CSV structure (exact matches)
ORGANIZATION_COLUMN = 'Organization'
ORGANIZATION_COUNTY_COLUMN = 'Organization County'
PRIMARY_COUNTY_COLUMN = 'Primary_County'
SERVICE_AREA_COLUMN = 'Service_Area'
MULTI_COUNTY_FLAG_COLUMN = 'Multi_County_Flag'
ROLE_POSITION_COLUMN = 'Role/Position'
ROLE_STANDARDIZED_COLUMN = 'Role_Standardized'
ROLE_CATEGORY_COLUMN = 'Role_Category'
ROLE_LEVEL_COLUMN = 'Role_Level'
ROLE_TYPE_COLUMN = 'Role_Type'
TIME_IN_POSITION_COLUMN = 'Length of time in current position'
TIME_RANGE_CATEGORY_COLUMN = 'Time_Range_Category'
EMAIL_COLUMN = 'Contact Email'
CONSENT_COLUMN = 'I consent to being contacted by a member of the Heartland Whole Health Institute team for additional feedback regarding my responses'

# Column name patterns for flexible matching (legacy)
ORG_COLUMN_PATTERNS = ['organization']
COUNTY_COLUMN_PATTERNS = ['county', 'Primary_County', 'Organization County']
ROLE_COLUMN_PATTERNS = ['role', 'position', 'Role_Standardized']
TIME_COLUMN_PATTERNS = ['time', 'Time_Range_Category']
EMAIL_COLUMN_PATTERNS = ['email']

# Exclude columns from text analysis
EXCLUDE_PATTERNS = ['time', 'email', 'consent', 'organization', 'county', 'role', 'position', 
                   'Start time', 'Completion time', 'Multi_County_Flag', 'Role_Category', 
                   'Role_Level', 'Role_Type', 'Time_Range_Category', 'Service_Area']

print("📋 Configuration loaded successfully!")
