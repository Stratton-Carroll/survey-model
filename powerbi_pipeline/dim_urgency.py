"""
Urgency Dimension Table Creation
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from healthcare_taxonomy import URGENCY_INDICATORS

def create_urgency_dimension():
    """Create the urgency dimension table"""
    
    dim_urgency = []
    urgency_id = 1
    
    for urgency_key, urgency_info in URGENCY_INDICATORS.items():
        dim_urgency.append({
            'UrgencyID': urgency_id,
            'UrgencyKey': urgency_key,
            'UrgencyLevel': urgency_key.title(),
            'UrgencyDescription': urgency_info['description'],
            'UrgencyScore': urgency_info['score']
        })
        urgency_id += 1
    
    # Add 'unknown' level
    dim_urgency.append({
        'UrgencyID': urgency_id,
        'UrgencyKey': 'unknown',
        'UrgencyLevel': 'Unknown',
        'UrgencyDescription': 'Urgency level could not be determined',
        'UrgencyScore': 1.5
    })
    
    df = pd.DataFrame(dim_urgency)
    print(f"⚡ Created DimUrgency with {len(df)} urgency levels")
    
    return df

if __name__ == "__main__":
    # Test the dimension creation
    dim_df = create_urgency_dimension()
    print(dim_df)
