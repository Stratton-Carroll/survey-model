"""
Healthcare Category Dimension Table Creation
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from healthcare_taxonomy import HEALTHCARE_CATEGORIES

def create_healthcare_category_dimension():
    """Create the healthcare category dimension table"""
    
    dim_category = []
    category_id = 1
    
    for category_key, category_info in HEALTHCARE_CATEGORIES.items():
        dim_category.append({
            'CategoryID': category_id,
            'CategoryKey': category_key,
            'CategoryName': category_key.replace('_', ' ').title(),
            'CategoryDescription': category_info['description'],
            'Domain': category_info['domain'],
            'PriorityWeight': category_info['priority_weight'],
            'KeywordCount': len(category_info['keywords'])
        })
        category_id += 1
    
    df = pd.DataFrame(dim_category)
    print(f"🏥 Created DimHealthcareCategory with {len(df)} categories")
    
    return df

if __name__ == "__main__":
    # Test the dimension creation
    dim_df = create_healthcare_category_dimension()
    print(dim_df.head())
