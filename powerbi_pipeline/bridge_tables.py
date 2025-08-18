"""
Bridge Tables Creation
Handles many-to-many relationships
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

def create_bridge_tables(processed_responses, dim_healthcare_category):
    """Create bridge tables for many-to-many relationships"""
    
    bridge_categories = []
    bridge_roles = []
    
    for i, response_data in enumerate(processed_responses):
        response_id = i + 1
        
        # Create category bridge records
        for category in response_data['categories']:
            # Find category ID
            category_matches = dim_healthcare_category[dim_healthcare_category['CategoryKey'] == category]
            if len(category_matches) > 0:
                category_id = category_matches.iloc[0]['CategoryID']
                bridge_categories.append({
                    'ResponseID': response_id,
                    'CategoryID': category_id
                })
        
        # Create role bridge records
        for role in response_data['healthcare_roles']:
            bridge_roles.append({
                'ResponseID': response_id,
                'RoleType': role,
                'RoleCategory': 'Healthcare'  # Simplified
            })
    
    bridge_cat_df = pd.DataFrame(bridge_categories)
    bridge_role_df = pd.DataFrame(bridge_roles)
    
    print(f"🔗 Created BridgeResponseCategories with {len(bridge_cat_df)} records")
    print(f"🔗 Created BridgeResponseRoles with {len(bridge_role_df)} records")
    
    return bridge_cat_df, bridge_role_df

if __name__ == "__main__":
    # Test bridge table creation
    print("Testing bridge table creation...")
    test_data = [{'categories': ['training', 'clinical'], 'healthcare_roles': ['nursing']}]
    dim_cat = pd.DataFrame([{'CategoryID': 1, 'CategoryKey': 'training'}, 
                           {'CategoryID': 2, 'CategoryKey': 'clinical'}])
    
    bridge_cat, bridge_role = create_bridge_tables(test_data, dim_cat)
    print("Categories bridge:", bridge_cat)
    print("Roles bridge:", bridge_role)
