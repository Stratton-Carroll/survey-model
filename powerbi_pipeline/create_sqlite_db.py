"""
Create SQLite Database from Power BI Data Model
Enables fast SQL querying for analysis and iteration
"""

import sqlite3
import pandas as pd
import os
import sys

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from config import OUTPUT_DIR
from backup_manual_overrides import backup_manual_overrides, restore_manual_overrides
from import_hierarchical_tags import import_tag_hierarchy, import_question_tag_mappings

def create_survey_database():
    """Create SQLite database from CSV files"""
    
    db_path = os.path.join(OUTPUT_DIR, 'survey_analysis.db')
    
    # Backup manual overrides before removing database
    print("💾 Backing up manual tag overrides...")
    backup_manual_overrides()
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️ Removed existing database")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    print(f"📊 Created SQLite database: {db_path}")
    
    try:
        # Load each CSV file into a table
        csv_files = {
            'DimGeography': 'DimGeography.csv',
            'DimOrganization': 'DimOrganization.csv', 
            'DimRole': 'DimRole.csv',
            'DimQuestion': 'DimQuestion.csv',
            'DimTags': 'DimTags.csv',
            'DimUrgency': 'DimUrgency.csv',
            'DimHealthcareCategory': 'DimHealthcareCategory.csv',
            'FactSurveyResponses': 'FactSurveyResponses.csv',
            'BridgeResponseTags': 'BridgeResponseTags.csv',
            'BridgeResponseCategories': 'BridgeResponseCategories.csv',
            'BridgeResponseRoles': 'BridgeResponseRoles.csv'
        }
        
        for table_name, csv_file in csv_files.items():
            csv_path = os.path.join(OUTPUT_DIR, csv_file)
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                print(f"✅ {table_name}: {len(df)} records loaded")
            else:
                print(f"⚠️ {csv_file} not found, skipping...")
        
        # Create helpful views for common queries
        create_analysis_views(conn)
        
        # Create some indexes for better performance
        create_indexes(conn)
        
        # Create ManualTagOverrides table
        create_manual_overrides_table(conn)
        
        conn.commit()
        print(f"🎉 Database created successfully!")
        print(f"📍 Location: {db_path}")
        
        # Restore manual overrides from backup
        conn.close()
        print("🔄 Restoring manual tag overrides from backup...")
        restore_manual_overrides()
        
        # Import hierarchical tags and question mappings
        print("🌳 Importing hierarchical tags...")
        import_tag_hierarchy()
        print("📊 Importing question-tag mappings...")
        import_question_tag_mappings()
        
        return db_path
        
    except Exception as e:
        print(f"❌ Error creating database: {str(e)}")
        return None
    finally:
        conn.close()

def create_analysis_views(conn):
    """Create helpful views for common analysis patterns"""
    
    views = {
        'ResponsesWithTags': """
        CREATE VIEW ResponsesWithTags AS
        SELECT 
            f.ResponseID,
            f.SurveyResponseNumber,
            f.ResponseText,
            f.ResponseLength,
            f.WordCount,
            dq.QuestionShort,
            dq.QuestionType,
            do.OrganizationName,
            do.OrganizationType,
            dg.PrimaryCounty,
            dg.Region,
            dr.RoleStandardized,
            dr.RoleCategory,
            dr.RoleLevel,
            dt.TagName,
            dt.TagCategory,
            dt.TagPriority
        FROM FactSurveyResponses f
        LEFT JOIN DimQuestion dq ON f.QuestionID = dq.QuestionID
        LEFT JOIN DimOrganization do ON f.OrganizationID = do.OrganizationID  
        LEFT JOIN DimGeography dg ON f.GeographyID = dg.GeographyID
        LEFT JOIN DimRole dr ON f.RoleID = dr.RoleID
        LEFT JOIN BridgeResponseTags bt ON f.ResponseID = bt.ResponseID
        LEFT JOIN DimTags dt ON bt.TagID = dt.TagID
        WHERE f.HasResponse = 1
        """,
        
        'TagSummary': """
        CREATE VIEW TagSummary AS
        SELECT 
            dt.TagName,
            dt.TagCategory,
            dt.TagPriority,
            COUNT(bt.ResponseID) as MentionCount,
            COUNT(DISTINCT f.SurveyResponseNumber) as UniqueSurveys,
            ROUND(AVG(f.ResponseLength), 1) as AvgResponseLength
        FROM DimTags dt
        LEFT JOIN BridgeResponseTags bt ON dt.TagID = bt.TagID
        LEFT JOIN FactSurveyResponses f ON bt.ResponseID = f.ResponseID
        GROUP BY dt.TagID, dt.TagName, dt.TagCategory, dt.TagPriority
        ORDER BY MentionCount DESC
        """,
        
        'RoleTagAnalysis': """
        CREATE VIEW RoleTagAnalysis AS
        SELECT 
            dr.RoleCategory,
            dr.RoleLevel,
            dt.TagName,
            dt.TagCategory as TagCategory,
            COUNT(bt.ResponseID) as Mentions,
            COUNT(DISTINCT f.SurveyResponseNumber) as UniqueSurveys
        FROM DimRole dr
        JOIN FactSurveyResponses f ON dr.RoleID = f.RoleID
        JOIN BridgeResponseTags bt ON f.ResponseID = bt.ResponseID
        JOIN DimTags dt ON bt.TagID = dt.TagID
        WHERE f.HasResponse = 1
        GROUP BY dr.RoleCategory, dr.RoleLevel, dt.TagName, dt.TagCategory
        ORDER BY Mentions DESC
        """,
        
        'QuestionTagAnalysis': """
        CREATE VIEW QuestionTagAnalysis AS
        SELECT 
            dq.QuestionShort,
            dq.QuestionType,
            dt.TagName,
            dt.TagCategory,
            COUNT(bt.ResponseID) as Mentions,
            ROUND(AVG(f.ResponseLength), 1) as AvgResponseLength
        FROM DimQuestion dq
        JOIN FactSurveyResponses f ON dq.QuestionID = f.QuestionID
        JOIN BridgeResponseTags bt ON f.ResponseID = bt.ResponseID
        JOIN DimTags dt ON bt.TagID = dt.TagID
        WHERE f.HasResponse = 1
        GROUP BY dq.QuestionShort, dq.QuestionType, dt.TagName, dt.TagCategory
        ORDER BY Mentions DESC
        """
    }
    
    for view_name, view_sql in views.items():
        try:
            conn.execute(view_sql)
            print(f"📋 Created view: {view_name}")
        except Exception as e:
            print(f"⚠️ Error creating view {view_name}: {str(e)}")

def create_indexes(conn):
    """Create indexes for better query performance"""
    
    indexes = [
        "CREATE INDEX idx_fact_response_id ON FactSurveyResponses(ResponseID)",
        "CREATE INDEX idx_fact_survey_number ON FactSurveyResponses(SurveyResponseNumber)", 
        "CREATE INDEX idx_bridge_tags_response ON BridgeResponseTags(ResponseID)",
        "CREATE INDEX idx_bridge_tags_tag ON BridgeResponseTags(TagID)",
        "CREATE INDEX idx_tags_category ON DimTags(TagCategory)",
        "CREATE INDEX idx_role_category ON DimRole(RoleCategory)",
        "CREATE INDEX idx_question_type ON DimQuestion(QuestionType)"
    ]
    
    for index_sql in indexes:
        try:
            conn.execute(index_sql)
        except Exception as e:
            print(f"⚠️ Index creation warning: {str(e)}")
    
    print("🔍 Created performance indexes")

def create_manual_overrides_table(conn):
    """Create ManualTagOverrides table for manual tag modifications"""
    
    create_table_sql = """
    CREATE TABLE ManualTagOverrides (
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
    
    try:
        conn.execute(create_table_sql)
        conn.execute("CREATE INDEX idx_manual_overrides_response ON ManualTagOverrides(SurveyResponseNumber, QuestionID)")
        conn.execute("CREATE INDEX idx_manual_overrides_tag ON ManualTagOverrides(TagID)")
        print("🏷️ Created ManualTagOverrides table")
    except Exception as e:
        print(f"⚠️ Error creating ManualTagOverrides table: {str(e)}")

def run_sample_queries(db_path):
    """Run some sample queries to demonstrate functionality"""
    
    conn = sqlite3.connect(db_path)
    
    print("\n" + "="*60)
    print("🔍 SAMPLE ANALYSIS QUERIES")
    print("="*60)
    
    queries = {
        "Top 5 Most Mentioned Tags": """
        SELECT TagName, TagCategory, MentionCount, UniqueSurveys 
        FROM TagSummary 
        ORDER BY MentionCount DESC 
        LIMIT 5
        """,
        
        "Tags by Role Category": """
        SELECT 
            RoleCategory,
            COUNT(DISTINCT TagName) as UniqueTagsMentioned,
            SUM(Mentions) as TotalMentions
        FROM RoleTagAnalysis 
        GROUP BY RoleCategory 
        ORDER BY TotalMentions DESC
        """,
        
        "High Priority Tags": """
        SELECT TagName, TagCategory, MentionCount
        FROM TagSummary 
        WHERE TagPriority = 'High'
        ORDER BY MentionCount DESC
        """,
        
        "NWA vs Non-NWA Themes": """
        SELECT 
            CASE WHEN dg.IsNWA = 1 THEN 'NWA' ELSE 'Non-NWA' END as Region,
            dt.TagCategory,
            COUNT(bt.ResponseID) as Mentions
        FROM FactSurveyResponses f
        JOIN DimGeography dg ON f.GeographyID = dg.GeographyID
        JOIN BridgeResponseTags bt ON f.ResponseID = bt.ResponseID
        JOIN DimTags dt ON bt.TagID = dt.TagID
        WHERE f.HasResponse = 1
        GROUP BY dg.IsNWA, dt.TagCategory
        ORDER BY Region, Mentions DESC
        """
    }
    
    for query_name, sql in queries.items():
        print(f"\n📊 {query_name}:")
        print("-" * 40)
        try:
            df = pd.read_sql_query(sql, conn)
            print(df.to_string(index=False))
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    conn.close()

if __name__ == "__main__":
    # Create the database
    db_path = create_survey_database()
    
    if db_path:
        # Run sample queries
        run_sample_queries(db_path)
        
        print(f"\n🎯 DATABASE READY FOR ANALYSIS!")
        print(f"📍 Database location: {db_path}")
        print(f"💡 Connect with: sqlite3 {db_path}")
        print(f"📋 Available tables: FactSurveyResponses, DimTags, BridgeResponseTags, etc.")
        print(f"🔍 Available views: ResponsesWithTags, TagSummary, RoleTagAnalysis, QuestionTagAnalysis")
