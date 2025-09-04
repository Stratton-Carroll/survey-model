#!/usr/bin/env python3
"""
Backup Manual Tag Overrides
Creates a backup of the ManualTagOverrides table before database rebuilds
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from config import OUTPUT_DIR

def backup_manual_overrides():
    """Export ManualTagOverrides and QuestionTagMappings tables to CSV for backup"""
    
    db_path = os.path.join(OUTPUT_DIR, 'survey_analysis.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found, no backup needed")
        return False
    
    conn = sqlite3.connect(db_path)
    
    # Check if ManualTagOverrides table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ManualTagOverrides'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        print("❌ ManualTagOverrides table not found, no backup needed")
        conn.close()
        return False
    
    # Export tables to CSV
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_success = False
        
        # Backup ManualTagOverrides
        df_manual = pd.read_sql_query("SELECT * FROM ManualTagOverrides", conn)
        if len(df_manual) > 0:
            backup_filename = f"ManualTagOverrides_backup_{timestamp}.csv"
            backup_path = os.path.join(OUTPUT_DIR, backup_filename)
            df_manual.to_csv(backup_path, index=False)
            
            latest_backup_path = os.path.join(OUTPUT_DIR, "ManualTagOverrides_latest.csv")
            df_manual.to_csv(latest_backup_path, index=False)
            
            print(f"✅ Backed up {len(df_manual)} manual tag overrides")
            backup_success = True
        
        # Backup QuestionTagMappings (if exists)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='QuestionTagMappings'")
        if cursor.fetchone():
            df_question = pd.read_sql_query("SELECT * FROM QuestionTagMappings", conn)
            if len(df_question) > 0:
                backup_filename = f"QuestionTagMappings_backup_{timestamp}.csv"
                backup_path = os.path.join(OUTPUT_DIR, backup_filename)
                df_question.to_csv(backup_path, index=False)
                
                latest_backup_path = os.path.join(OUTPUT_DIR, "QuestionTagMappings_latest.csv")
                df_question.to_csv(latest_backup_path, index=False)
                
                print(f"✅ Backed up {len(df_question)} question-tag mappings")
                backup_success = True
        
        # Backup hierarchical DimTags structure
        df_tags = pd.read_sql_query("SELECT * FROM DimTags WHERE ParentTagID IS NOT NULL OR TagLevel = 1", conn)
        if len(df_tags) > 0:
            backup_filename = f"DimTags_hierarchical_backup_{timestamp}.csv"
            backup_path = os.path.join(OUTPUT_DIR, backup_filename)
            df_tags.to_csv(backup_path, index=False)
            
            latest_backup_path = os.path.join(OUTPUT_DIR, "DimTags_hierarchical_latest.csv")
            df_tags.to_csv(latest_backup_path, index=False)
            
            print(f"✅ Backed up {len(df_tags)} hierarchical tags")
            backup_success = True
        
        if not backup_success:
            print("📝 No custom data to backup")
        
        conn.close()
        return backup_success
        
    except Exception as e:
        print(f"❌ Error backing up ManualTagOverrides: {e}")
        conn.close()
        return False

def restore_manual_overrides(backup_file=None):
    """Restore ManualTagOverrides from backup CSV"""
    
    db_path = os.path.join(OUTPUT_DIR, 'survey_analysis.db')
    
    if backup_file is None:
        backup_file = os.path.join(OUTPUT_DIR, "ManualTagOverrides_latest.csv")
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Read backup CSV
        df = pd.read_csv(backup_file)
        print(f"📂 Found {len(df)} records in backup file")
        
        # Create table if it doesn't exist
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ManualTagOverrides (
            OverrideID INTEGER PRIMARY KEY AUTOINCREMENT,
            SurveyResponseNumber INTEGER NOT NULL,
            QuestionID INTEGER NOT NULL,
            TagID INTEGER NOT NULL,
            Action TEXT CHECK(Action IN ('ADD', 'REMOVE')) NOT NULL,
            AppliedBy TEXT NOT NULL,
            AppliedDate TEXT NOT NULL,
            Notes TEXT,
            IsActive INTEGER DEFAULT 1,
            FOREIGN KEY (TagID) REFERENCES DimTags(TagID)
        )
        """
        conn.execute(create_table_sql)
        
        # Clear existing data
        conn.execute("DELETE FROM ManualTagOverrides")
        
        # Import backup data
        df.to_sql('ManualTagOverrides', conn, if_exists='append', index=False)
        conn.commit()
        
        print(f"✅ Restored {len(df)} manual tag overrides from backup")
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error restoring ManualTagOverrides: {e}")
        conn.close()
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        backup_file = sys.argv[2] if len(sys.argv) > 2 else None
        restore_manual_overrides(backup_file)
    else:
        backup_manual_overrides()