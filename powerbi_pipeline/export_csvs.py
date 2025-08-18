"""
CSV Export Module
Handles exporting all tables to CSV files for Power BI
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config import OUTPUT_DIR

def export_all_tables(tables_dict):
    """Export all tables to CSV files"""
    
    exported_files = []
    
    for table_name, dataframe in tables_dict.items():
        if dataframe is not None and len(dataframe) > 0:
            file_path = os.path.join(OUTPUT_DIR, f"{table_name}.csv")
            dataframe.to_csv(file_path, index=False, encoding='utf-8')
            exported_files.append(file_path)
            print(f"✅ {table_name}: {len(dataframe)} rows → {file_path}")
        else:
            print(f"⚠️ Skipped {table_name}: No data")
    
    # Create a simple import instructions file
    instructions_file = os.path.join(OUTPUT_DIR, "PowerBI_Import_Instructions.txt")
    with open(instructions_file, 'w') as f:
        f.write("Power BI Import Instructions\\n")
        f.write("=========================\\n\\n")
        f.write("1. Open Power BI Desktop\\n")
        f.write("2. Get Data > Text/CSV\\n")
        f.write("3. Import each CSV file as a separate table\\n\\n")
        f.write("Recommended import order:\\n")
        for table_name in tables_dict.keys():
            f.write(f"- {table_name}.csv\\n")
        f.write("\\n4. Create relationships between tables in Model view\\n")
        f.write("5. Build your dashboard using the dimensional model\\n")
    
    exported_files.append(instructions_file)
    print(f"📖 Import instructions: {instructions_file}")
    
    return exported_files

if __name__ == "__main__":
    # Test export functionality
    test_tables = {
        'TestTable': pd.DataFrame({'ID': [1, 2], 'Name': ['A', 'B']})
    }
    export_all_tables(test_tables)
