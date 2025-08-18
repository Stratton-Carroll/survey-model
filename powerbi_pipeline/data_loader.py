"""
Data loading and initial processing
Handles Excel file loading and basic data validation
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config import DATA_FILE

def load_survey_data():
    """Load the survey data from CSV file"""
    try:
        df = pd.read_csv(DATA_FILE, encoding='utf-8')
        print(f"✅ Loaded survey data: {df.shape[0]} responses, {df.shape[1]} columns")
        
        # Display basic info about the data
        print(f"   📝 Columns: {list(df.columns[:5])}..." if len(df.columns) > 5 else f"   📝 Columns: {list(df.columns)}")
        return df
    except FileNotFoundError:
        print(f"❌ Error: Could not find data file: {DATA_FILE}")
        return None
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        return None

def get_column_by_pattern(df, patterns):
    """Find column that matches any of the given patterns"""
    for col in df.columns:
        col_lower = col.lower()
        for pattern in patterns:
            if pattern in col_lower:
                return col
    return None

def identify_open_ended_columns(df):
    """Identify columns that contain open-ended text responses"""
    from config import EXCLUDE_PATTERNS
    
    open_ended_cols = []
    for col in df.columns:
        # Check if it's an object (text) column
        if df[col].dtype == 'object':
            # Check if it's not an excluded pattern
            col_lower = col.lower()
            is_excluded = any(pattern.lower() in col_lower for pattern in EXCLUDE_PATTERNS)
            
            # Also exclude exact matches to structured columns
            exact_excludes = ['Organization', 'Organization County', 'Primary_County', 
                            'Service_Area', 'Role/Position', 'Role_Standardized', 
                            'Role_Category', 'Role_Level', 'Role_Type', 
                            'Length of time in current position', 'Time_Range_Category',
                            'Contact Email', 'Multi_County_Flag']
            is_exact_excluded = col in exact_excludes
            
            if not is_excluded and not is_exact_excluded:
                # Check if it has meaningful responses (not just single words)
                sample_responses = df[col].dropna().head(10)
                if len(sample_responses) > 0:
                    avg_length = sample_responses.astype(str).str.len().mean()
                    if avg_length > 30:  # Increased threshold for meaningful text responses
                        open_ended_cols.append(col)
    
    return open_ended_cols

def validate_data(df):
    """Perform basic data validation"""
    validation_results = {
        'total_responses': len(df),
        'total_columns': len(df.columns),
        'missing_data_summary': df.isnull().sum().sum(),
        'response_rate_by_column': {}
    }
    
    for col in df.columns:
        response_rate = (df[col].notna().sum() / len(df)) * 100
        validation_results['response_rate_by_column'][col] = round(response_rate, 1)
    
    return validation_results

if __name__ == "__main__":
    # Test the data loader
    df = load_survey_data()
    if df is not None:
        validation = validate_data(df)
        print(f"📊 Validation results:")
        print(f"   Total responses: {validation['total_responses']}")
        print(f"   Total columns: {validation['total_columns']}")
        print(f"   Missing data points: {validation['missing_data_summary']}")
        
        open_ended = identify_open_ended_columns(df)
        print(f"   Open-ended questions identified: {len(open_ended)}")
        
        print("✅ Data loader test completed successfully!")
