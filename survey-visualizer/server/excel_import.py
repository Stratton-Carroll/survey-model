#!/usr/bin/env python3
"""
Excel Import Functionality for Question-Based Tag Assignments
Supports bulk assignment of primary tags and sub-tags to questions
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os

class TagAssignmentImporter:
    def __init__(self, database_path):
        self.database_path = database_path
        
    def get_db_connection(self):
        """Create database connection"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def validate_excel_structure(self, df):
        """Validate Excel file has required columns"""
        required_columns = ['QuestionID', 'TagName', 'TagType', 'AssignmentType']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Validate data types and values
        if not df['QuestionID'].dtype in ['int64', 'int32']:
            raise ValueError("QuestionID must be integer values")
            
        valid_tag_types = ['Primary', 'Sub']
        invalid_tag_types = df[~df['TagType'].isin(valid_tag_types)]['TagType'].unique()
        if len(invalid_tag_types) > 0:
            raise ValueError(f"Invalid TagType values: {invalid_tag_types}. Must be: {valid_tag_types}")
            
        valid_assignment_types = ['AUTOMATIC', 'CONDITIONAL', 'SUGGESTED']  
        invalid_assignment_types = df[~df['AssignmentType'].isin(valid_assignment_types)]['AssignmentType'].unique()
        if len(invalid_assignment_types) > 0:
            raise ValueError(f"Invalid AssignmentType values: {invalid_assignment_types}. Must be: {valid_assignment_types}")
        
        return True
    
    def validate_tags_exist(self, df):
        """Validate all TagNames exist in DimTags table"""
        conn = self.get_db_connection()
        
        # Get all valid tag names from database
        existing_tags_query = "SELECT TagName FROM DimTags WHERE IsActive = 1"
        existing_tags = pd.read_sql_query(existing_tags_query, conn)
        existing_tag_names = set(existing_tags['TagName'].tolist())
        
        # Check for invalid tag names in Excel
        excel_tag_names = set(df['TagName'].tolist())
        invalid_tags = excel_tag_names - existing_tag_names
        
        conn.close()
        
        if invalid_tags:
            raise ValueError(f"Invalid TagNames not found in database: {invalid_tags}")
        
        return True
    
    def validate_tag_hierarchy(self, df):
        """Validate Primary/Sub tag relationships are correct"""
        conn = self.get_db_connection()
        
        # Get tag hierarchy from database
        hierarchy_query = """
        SELECT TagName, TagLevel, ParentTagID, 
               (SELECT TagName FROM DimTags p WHERE p.TagID = s.ParentTagID) as ParentTagName
        FROM DimTags s 
        WHERE IsActive = 1
        """
        hierarchy_df = pd.read_sql_query(hierarchy_query, conn)
        conn.close()
        
        # Validate each row in Excel
        for _, row in df.iterrows():
            tag_name = row['TagName']
            declared_type = row['TagType']
            
            # Find tag in hierarchy
            tag_info = hierarchy_df[hierarchy_df['TagName'] == tag_name]
            if tag_info.empty:
                continue  # Will be caught by validate_tags_exist
                
            tag_level = tag_info.iloc[0]['TagLevel']
            parent_tag_name = tag_info.iloc[0]['ParentTagName']
            
            # Validate declared type matches actual type
            actual_type = 'Primary' if tag_level == 1 else 'Sub'
            if declared_type != actual_type:
                raise ValueError(f"Tag '{tag_name}' is declared as '{declared_type}' but is actually '{actual_type}' in database")
        
        return True
    
    def import_from_excel(self, excel_file_path, applied_by="Excel Import", dry_run=False):
        """
        Import question-tag mappings from Excel file
        
        Args:
            excel_file_path: Path to Excel file
            applied_by: Who is performing the import  
            dry_run: If True, validates but doesn't insert data
            
        Returns:
            dict with import results
        """
        results = {
            'success': False,
            'records_processed': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Read Excel file
            if not os.path.exists(excel_file_path):
                raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
                
            df = pd.read_excel(excel_file_path, sheet_name=0)
            results['records_processed'] = len(df)
            
            # Fill optional columns if missing
            if 'Notes' not in df.columns:
                df['Notes'] = ''
            if 'AppliedBy' not in df.columns:
                df['AppliedBy'] = applied_by
            
            # Validation steps
            self.validate_excel_structure(df)
            self.validate_tags_exist(df)  
            self.validate_tag_hierarchy(df)
            
            if dry_run:
                results['success'] = True
                results['warnings'].append("Dry run completed - no data was imported")
                return results
            
            # Perform import
            conn = self.get_db_connection()
            current_time = datetime.now().isoformat()
            
            inserted_count = 0
            updated_count = 0
            
            for _, row in df.iterrows():
                # Get TagID from TagName
                tag_query = "SELECT TagID FROM DimTags WHERE TagName = ? AND IsActive = 1"
                tag_result = conn.execute(tag_query, (row['TagName'],)).fetchone()
                
                if not tag_result:
                    results['errors'].append(f"TagName '{row['TagName']}' not found")
                    continue
                    
                tag_id = tag_result['TagID']
                
                # Check if mapping already exists
                exists_query = "SELECT COUNT(*) as count FROM QuestionTagMappings WHERE QuestionID = ? AND TagID = ?"
                exists_result = conn.execute(exists_query, (row['QuestionID'], tag_id)).fetchone()
                
                if exists_result['count'] > 0:
                    # Update existing mapping
                    update_query = """
                    UPDATE QuestionTagMappings 
                    SET AssignmentType = ?, AppliedBy = ?, AppliedDate = ?, Notes = ?, IsActive = 1
                    WHERE QuestionID = ? AND TagID = ?
                    """
                    conn.execute(update_query, (
                        row['AssignmentType'], row['AppliedBy'], current_time, 
                        row['Notes'], row['QuestionID'], tag_id
                    ))
                    updated_count += 1
                else:
                    # Insert new mapping
                    insert_query = """
                    INSERT INTO QuestionTagMappings 
                    (QuestionID, TagID, AssignmentType, AppliedBy, AppliedDate, Notes, IsActive)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    """
                    conn.execute(insert_query, (
                        row['QuestionID'], tag_id, row['AssignmentType'],
                        row['AppliedBy'], current_time, row['Notes']
                    ))
                    inserted_count += 1
            
            conn.commit()
            conn.close()
            
            results['records_inserted'] = inserted_count
            results['records_updated'] = updated_count  
            results['success'] = True
            
        except Exception as e:
            results['errors'].append(str(e))
            
        return results
    
    def export_current_mappings(self, output_file_path):
        """Export current question-tag mappings to Excel for editing"""
        conn = self.get_db_connection()
        
        query = """
        SELECT 
            qtm.QuestionID,
            dt.TagName,
            CASE WHEN dt.TagLevel = 1 THEN 'Primary' ELSE 'Sub' END as TagType,
            qtm.AssignmentType,
            qtm.Notes,
            qtm.AppliedBy,
            qtm.AppliedDate
        FROM QuestionTagMappings qtm
        JOIN DimTags dt ON qtm.TagID = dt.TagID
        WHERE qtm.IsActive = 1 AND dt.IsActive = 1
        ORDER BY qtm.QuestionID, dt.TagLevel, dt.TagName
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='QuestionTagMappings', index=False)
            
        return len(df)

if __name__ == "__main__":
    # Example usage
    database_path = "../powerbi_data_model_v2/survey_analysis.db"
    importer = TagAssignmentImporter(database_path)
    
    # Example: validate and import
    # results = importer.import_from_excel("tag_mappings.xlsx", dry_run=True)
    # print(results)