#!/usr/bin/env python3
"""
Import Hierarchical Tags from Excel Files
1. Import tag structure (Primary -> Sub relationships)
2. Import tags_normalized.xlsx (Response -> Tag mappings)
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime
from config import OUTPUT_DIR

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(OUTPUT_DIR, 'survey_analysis.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def import_tag_hierarchy():
    """Import Primary -> Sub tag relationships"""
    print("📋 Importing tag hierarchy...")
    
    # Read tag structure
    structure_path = "/Users/strattoncarroll/Documents/survey-model/excel_templates/tag_structure.xlsx"
    df_structure = pd.read_excel(structure_path)
    
    conn = get_db_connection()
    
    # Get current max TagID
    max_tag_query = "SELECT MAX(TagID) as max_id FROM DimTags"
    max_result = conn.execute(max_tag_query).fetchone()
    next_tag_id = (max_result['max_id'] or 0) + 1
    
    # Track primary tag name to ID mapping
    primary_tag_map = {}
    
    # First pass: Create/update all primary tags
    primary_tags = df_structure['Primary Tag'].unique()
    
    for primary_tag in primary_tags:
        # Check if primary tag exists
        existing_query = "SELECT TagID FROM DimTags WHERE TagName = ? AND TagLevel = 1"
        existing = conn.execute(existing_query, (primary_tag,)).fetchone()
        
        if existing:
            primary_tag_map[primary_tag] = existing['TagID']
            print(f"✅ Primary tag exists: {primary_tag} (ID: {existing['TagID']})")
        else:
            # Create new primary tag
            insert_query = """
            INSERT INTO DimTags (TagID, TagName, TagCategory, TagLevel, ParentTagID, IsActive)
            VALUES (?, ?, ?, 1, NULL, 1)
            """
            conn.execute(insert_query, (next_tag_id, primary_tag, "New Category", ))
            primary_tag_map[primary_tag] = next_tag_id
            print(f"➕ Created primary tag: {primary_tag} (ID: {next_tag_id})")
            next_tag_id += 1
    
    # Second pass: Create sub-tags
    for _, row in df_structure.iterrows():
        primary_tag = row['Primary Tag']
        sub_tag = row['Subtag']
        parent_id = primary_tag_map[primary_tag]
        
        # Check if sub-tag exists
        existing_query = "SELECT TagID FROM DimTags WHERE TagName = ? AND ParentTagID = ?"
        existing = conn.execute(existing_query, (sub_tag, parent_id)).fetchone()
        
        if not existing:
            # Create new sub-tag
            insert_query = """
            INSERT INTO DimTags (TagID, TagName, TagCategory, TagLevel, ParentTagID, IsActive)
            VALUES (?, ?, ?, 2, ?, 1)
            """
            conn.execute(insert_query, (next_tag_id, sub_tag, "Sub Category", parent_id))
            print(f"   ↳ Created sub-tag: {sub_tag} (ID: {next_tag_id}, Parent: {parent_id})")
            next_tag_id += 1
        else:
            print(f"   ✅ Sub-tag exists: {sub_tag}")
    
    conn.commit()
    conn.close()
    print(f"🎉 Tag hierarchy imported successfully!")

def import_question_tag_mappings():
    """Import Response -> Tag mappings from tags_normalized.xlsx"""
    print("📊 Importing question-tag mappings...")
    
    # Read normalized tags
    normalized_path = "/Users/strattoncarroll/Documents/survey-model/excel_templates/tags_normalized.xlsx"
    df_normalized = pd.read_excel(normalized_path)
    
    conn = get_db_connection()
    
    current_time = datetime.now().isoformat()
    inserted_count = 0
    skipped_count = 0
    
    for _, row in df_normalized.iterrows():
        response_id = row['ResponseID']
        tag_name = row['TagName']
        tag_type = row['TagType']
        
        # Find TagID for this tag name (case-insensitive)
        tag_query = "SELECT TagID FROM DimTags WHERE LOWER(TagName) = LOWER(?) AND IsActive = 1"
        tag_result = conn.execute(tag_query, (tag_name,)).fetchone()
        
        if not tag_result:
            print(f"⚠️ Tag not found: {tag_name}")
            skipped_count += 1
            continue
        
        tag_id = tag_result['TagID']
        
        # Check if mapping already exists
        exists_query = "SELECT COUNT(*) as count FROM QuestionTagMappings WHERE ResponseID = ? AND TagID = ?"
        exists_result = conn.execute(exists_query, (response_id, tag_id)).fetchone()
        
        if exists_result['count'] > 0:
            skipped_count += 1
            continue
        
        # Insert new mapping
        insert_query = """
        INSERT INTO QuestionTagMappings 
        (ResponseID, TagID, TagType, AssignmentType, AppliedBy, AppliedDate, IsActive)
        VALUES (?, ?, ?, 'AUTOMATIC', 'Question-based Import', ?, 1)
        """
        conn.execute(insert_query, (response_id, tag_id, tag_type, current_time))
        inserted_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"📈 Imported {inserted_count} question-tag mappings")
    print(f"⏭️ Skipped {skipped_count} existing/invalid mappings")

def verify_import():
    """Verify the import results"""
    print("🔍 Verifying import results...")
    
    conn = get_db_connection()
    
    # Tag hierarchy stats
    primary_count = conn.execute("SELECT COUNT(*) as count FROM DimTags WHERE TagLevel = 1").fetchone()['count']
    sub_count = conn.execute("SELECT COUNT(*) as count FROM DimTags WHERE TagLevel = 2").fetchone()['count']
    
    # Mapping stats
    mapping_count = conn.execute("SELECT COUNT(*) as count FROM QuestionTagMappings").fetchone()['count']
    
    # Sample hierarchy
    sample_query = """
    SELECT p.TagName as PrimaryTag, s.TagName as SubTag
    FROM DimTags p
    LEFT JOIN DimTags s ON p.TagID = s.ParentTagID
    WHERE p.TagLevel = 1 AND s.TagLevel = 2
    ORDER BY p.TagName, s.TagName
    LIMIT 5
    """
    samples = conn.execute(sample_query).fetchall()
    
    conn.close()
    
    print(f"📊 Primary tags: {primary_count}")
    print(f"📋 Sub-tags: {sub_count}")
    print(f"🔗 Question mappings: {mapping_count}")
    print(f"\n🌳 Sample hierarchy:")
    for sample in samples:
        print(f"   {sample['PrimaryTag']} → {sample['SubTag']}")

if __name__ == "__main__":
    print("🚀 Starting hierarchical tags import...")
    print("="*50)
    
    try:
        # Step 1: Import tag hierarchy
        import_tag_hierarchy()
        print()
        
        # Step 2: Import question mappings
        import_question_tag_mappings()
        print()
        
        # Step 3: Verify results
        verify_import()
        
        print("\n✅ Hierarchical tags import completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        import traceback
        traceback.print_exc()