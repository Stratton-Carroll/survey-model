from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

# Use absolute path to the database
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(BASE_DIR, 'powerbi_data_model_v2', 'survey_analysis.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/tags', methods=['GET'])
def get_tags():
    try:
        print(f"Attempting to connect to database at: {DATABASE_PATH}")
        print(f"Database file exists: {os.path.exists(DATABASE_PATH)}")
        conn = get_db_connection()
        
        # Get tags with effective response counts (including manual overrides)
        query = """
        WITH EffectiveResponseTags AS (
            -- Original tags
            SELECT bt.TagID, bt.ResponseID
            FROM BridgeResponseTags bt
            
            UNION
            
            -- Manual additions
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE mto.Action = 'ADD'
            
            EXCEPT
            
            -- Manual removals
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE mto.Action = 'REMOVE'
        )
        SELECT t.TagID, t.TagKey, t.TagName, t.TagCategory, t.TagPriority, 
               t.TagDescription, t.IsActive, COUNT(ert.ResponseID) as ResponseCount 
        FROM DimTags t 
        LEFT JOIN EffectiveResponseTags ert ON t.TagID = ert.TagID 
        WHERE t.IsActive = 1
        GROUP BY t.TagID, t.TagKey, t.TagName, t.TagCategory, t.TagPriority, t.TagDescription, t.IsActive
        ORDER BY ResponseCount DESC
        """
        
        tags = conn.execute(query).fetchall()
        conn.close()
        return jsonify([dict(tag) for tag in tags])
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/questions/<int:question_id>/tag-distribution', methods=['GET'])
def get_question_tag_distribution(question_id):
    try:
        conn = get_db_connection()
        query = """
        WITH EffectiveResponseTags AS (
            -- Original tags for this question
            SELECT bt.TagID, bt.ResponseID
            FROM BridgeResponseTags bt
            JOIN FactSurveyResponses f ON bt.ResponseID = f.ResponseID
            WHERE f.QuestionID = ?
            
            UNION
            
            -- Manual additions for this question
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE f.QuestionID = ? AND mto.Action = 'ADD'
            
            EXCEPT
            
            -- Manual removals for this question
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE f.QuestionID = ? AND mto.Action = 'REMOVE'
        )
        SELECT 
            dt.TagID,
            dt.TagName,
            dt.TagCategory,
            COUNT(DISTINCT ert.ResponseID) as TagCount
        FROM EffectiveResponseTags ert
        JOIN DimTags dt ON ert.TagID = dt.TagID
        WHERE dt.IsActive = 1
        GROUP BY dt.TagID, dt.TagName, dt.TagCategory
        ORDER BY TagCount DESC
        """
        tag_distribution = conn.execute(query, (question_id, question_id, question_id)).fetchall()
        conn.close()
        return jsonify([dict(item) for item in tag_distribution])
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags/<int:tag_id>/responses', methods=['GET'])
def get_tag_responses(tag_id):
    try:
        conn = get_db_connection()
        
        query = """
        SELECT DISTINCT f.ResponseID, f.ResponseText, f.SurveyResponseNumber, q.QuestionText, q.QuestionShort,
               o.OrganizationName, o.OrganizationType, g.PrimaryCounty, g.State, 
               g.Region, r.RoleStandardized as RoleName
        FROM BridgeResponseTags bt
        JOIN FactSurveyResponses f ON bt.ResponseID = f.ResponseID
        JOIN DimQuestion q ON f.QuestionID = q.QuestionID
        LEFT JOIN DimOrganization o ON f.OrganizationID = o.OrganizationID
        LEFT JOIN DimGeography g ON f.GeographyID = g.GeographyID
        LEFT JOIN DimRole r ON f.RoleID = r.RoleID
        WHERE bt.TagID = ?
        ORDER BY f.SurveyResponseNumber
        """
        
        responses = conn.execute(query, (tag_id,)).fetchall()
        
        # For each response, get all effective tags (original + overrides)
        response_list = []
        for response in responses:
            # Get effective tags using the same logic as the dedicated endpoint
            effective_tags_query = """
            WITH EffectiveTags AS (
                -- Original tags
                SELECT bt.TagID
                FROM BridgeResponseTags bt
                WHERE bt.ResponseID = ?
                
                UNION
                
                -- Manual additions
                SELECT mto.TagID
                FROM ManualTagOverrides mto
                JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                    AND mto.QuestionID = f.QuestionID
                WHERE f.ResponseID = ? AND mto.Action = 'ADD'
                
                EXCEPT
                
                -- Manual removals
                SELECT mto.TagID
                FROM ManualTagOverrides mto
                JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                    AND mto.QuestionID = f.QuestionID
                WHERE f.ResponseID = ? AND mto.Action = 'REMOVE'
            )
            SELECT DISTINCT et.TagID, t.TagName, t.TagCategory
            FROM EffectiveTags et
            JOIN DimTags t ON et.TagID = t.TagID
            WHERE t.IsActive = 1
            ORDER BY t.TagName
            """
            tags = conn.execute(effective_tags_query, (response['ResponseID'], response['ResponseID'], response['ResponseID'])).fetchall()
            
            response_dict = dict(response)
            response_dict['Tags'] = [dict(tag) for tag in tags]
            response_list.append(response_dict)
        
        conn.close()
        return jsonify(response_list)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/responses', methods=['GET'])
def get_responses_with_tags():
    try:
        conn = get_db_connection()
        
        # Get all responses with their effective tags (including manual overrides)
        query = """
        SELECT 
            f.ResponseID,
            f.SurveyResponseNumber,
            f.ResponseText,
            q.QuestionID,
            q.QuestionText,
            q.QuestionShort,
            o.OrganizationName,
            o.OrganizationType,
            g.PrimaryCounty,
            g.State,
            r.RoleStandardized as RoleName
        FROM FactSurveyResponses f
        JOIN DimQuestion q ON f.QuestionID = q.QuestionID
        LEFT JOIN DimOrganization o ON f.OrganizationID = o.OrganizationID
        LEFT JOIN DimGeography g ON f.GeographyID = g.GeographyID
        LEFT JOIN DimRole r ON f.RoleID = r.RoleID
        WHERE f.HasResponse = 1 AND f.ResponseText IS NOT NULL AND f.ResponseText != ''
        ORDER BY q.QuestionID, f.SurveyResponseNumber
        """
        
        responses = conn.execute(query).fetchall()
        
        # Process the results to create a nested structure with effective tags
        result = {}
        for response in responses:
            question_id = response['QuestionID']
            if question_id not in result:
                result[question_id] = {
                    'QuestionID': question_id,
                    'QuestionText': response['QuestionText'],
                    'QuestionShort': response['QuestionShort'],
                    'responses': []
                }
            
            # Get effective tags for this response using the same logic as the dedicated endpoint
            effective_tags_query = """
            WITH EffectiveTags AS (
                -- Original tags
                SELECT bt.TagID
                FROM BridgeResponseTags bt
                WHERE bt.ResponseID = ?
                
                UNION
                
                -- Manual additions
                SELECT mto.TagID
                FROM ManualTagOverrides mto
                JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                    AND mto.QuestionID = f.QuestionID
                WHERE f.ResponseID = ? AND mto.Action = 'ADD'
                
                EXCEPT
                
                -- Manual removals
                SELECT mto.TagID
                FROM ManualTagOverrides mto
                JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                    AND mto.QuestionID = f.QuestionID
                WHERE f.ResponseID = ? AND mto.Action = 'REMOVE'
            )
            SELECT DISTINCT et.TagID, t.TagName, t.TagCategory
            FROM EffectiveTags et
            JOIN DimTags t ON et.TagID = t.TagID
            WHERE t.IsActive = 1
            ORDER BY t.TagName
            """
            tags_result = conn.execute(effective_tags_query, (response['ResponseID'], response['ResponseID'], response['ResponseID'])).fetchall()
            tags = [dict(tag) for tag in tags_result]
            
            result[question_id]['responses'].append({
                'ResponseID': response['ResponseID'],
                'SurveyResponseNumber': response['SurveyResponseNumber'],
                'ResponseText': response['ResponseText'],
                'OrganizationName': response['OrganizationName'],
                'OrganizationType': response['OrganizationType'],
                'PrimaryCounty': response['PrimaryCounty'],
                'State': response['State'],
                'RoleName': response['RoleName'],
                'Tags': tags
            })
        
        conn.close()
        return jsonify(list(result.values()))
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        conn = get_db_connection()
        analytics_data = {}
        
        # Overview metrics
        overview_query = """
        SELECT 
            COUNT(*) as total_responses,
            COUNT(DISTINCT SurveyResponseNumber) as unique_respondents,
            AVG(CAST(ResponseRate AS REAL)) as avg_response_rate,
            AVG(CASE WHEN HasResponse = 1 THEN WordCount END) as avg_word_count,
            AVG(CASE WHEN HasResponse = 1 THEN ResponseLength END) as avg_response_length
        FROM FactSurveyResponses f
        LEFT JOIN DimQuestion q ON f.QuestionID = q.QuestionID
        """
        overview = conn.execute(overview_query).fetchone()
        analytics_data['overview'] = dict(overview)
        
        # Role category analysis
        role_category_query = """
        SELECT r.RoleCategory, COUNT(*) as response_count
        FROM FactSurveyResponses f
        JOIN DimRole r ON f.RoleID = r.RoleID
        GROUP BY r.RoleCategory
        ORDER BY response_count DESC
        """
        role_categories = conn.execute(role_category_query).fetchall()
        analytics_data['role_category_analysis'] = [dict(row) for row in role_categories]
        
        # Tag category analysis
        tag_category_query = """
        SELECT t.TagCategory, COUNT(*) as count
        FROM DimTags t
        WHERE t.IsActive = 1
        GROUP BY t.TagCategory
        ORDER BY count DESC
        """
        tag_categories = conn.execute(tag_category_query).fetchall()
        analytics_data['tag_category_analysis'] = [dict(row) for row in tag_categories]
        
        # Healthcare domain analysis
        healthcare_domain_query = """
        SELECT Domain, COUNT(*) as count
        FROM DimHealthcareCategory
        GROUP BY Domain
        ORDER BY count DESC
        """
        healthcare_domains = conn.execute(healthcare_domain_query).fetchall()
        analytics_data['healthcare_domain_analysis'] = [dict(row) for row in healthcare_domains]
        
        # Question type analysis
        question_type_query = """
        SELECT QuestionType, COUNT(*) as count
        FROM DimQuestion
        GROUP BY QuestionType
        ORDER BY count DESC
        """
        question_types = conn.execute(question_type_query).fetchall()
        analytics_data['question_type_analysis'] = [dict(row) for row in question_types]
        
        # Response quality insights
        response_quality_query = """
        SELECT 
            COUNT(CASE WHEN ResponseRate > 80 THEN 1 END) as high_engagement_count,
            COUNT(CASE WHEN WordCount > 50 AND HasResponse = 1 THEN 1 END) as detailed_responses_count,
            ROUND(
                CAST(SUM(CASE WHEN IsOpenEnded = 1 THEN 1 ELSE 0 END) AS REAL) / 
                CAST(COUNT(*) AS REAL) * 100, 1
            ) as text_question_ratio
        FROM DimQuestion q
        LEFT JOIN FactSurveyResponses f ON q.QuestionID = f.QuestionID
        """
        response_quality = conn.execute(response_quality_query).fetchone()
        analytics_data['response_quality'] = dict(response_quality)
        
        # Priority areas (top tags by effective response count)
        priority_areas_query = """
        WITH EffectiveResponseTags AS (
            -- Original tags
            SELECT bt.TagID, bt.ResponseID
            FROM BridgeResponseTags bt
            
            UNION
            
            -- Manual additions
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE mto.Action = 'ADD'
            
            EXCEPT
            
            -- Manual removals
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE mto.Action = 'REMOVE'
        )
        SELECT t.TagID, t.TagName, t.TagDescription, t.TagCategory, COUNT(ert.ResponseID) as ResponseCount
        FROM DimTags t
        LEFT JOIN EffectiveResponseTags ert ON t.TagID = ert.TagID
        WHERE t.IsActive = 1
        GROUP BY t.TagID, t.TagName, t.TagDescription, t.TagCategory
        ORDER BY ResponseCount DESC
        LIMIT 10
        """
        priority_areas = conn.execute(priority_areas_query).fetchall()
        analytics_data['priority_areas'] = [dict(row) for row in priority_areas]
        
        # Filtered tag analysis by role category using effective tags
        filtered_tag_query = """
        WITH EffectiveResponseTags AS (
            -- Original tags
            SELECT bt.TagID, bt.ResponseID
            FROM BridgeResponseTags bt
            
            UNION
            
            -- Manual additions
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE mto.Action = 'ADD'
            
            EXCEPT
            
            -- Manual removals
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE mto.Action = 'REMOVE'
        )
        SELECT 
            r.RoleCategory,
            t.TagName,
            COUNT(ert.ResponseID) as ResponseCount
        FROM FactSurveyResponses f
        JOIN DimRole r ON f.RoleID = r.RoleID
        JOIN EffectiveResponseTags ert ON f.ResponseID = ert.ResponseID
        JOIN DimTags t ON ert.TagID = t.TagID
        WHERE t.IsActive = 1
        GROUP BY r.RoleCategory, t.TagName
        ORDER BY r.RoleCategory, ResponseCount DESC
        """
        filtered_tags = conn.execute(filtered_tag_query).fetchall()
        
        # Organize filtered tags by role category
        filtered_tag_analysis = {}
        for row in filtered_tags:
            role_category = row['RoleCategory']
            if role_category not in filtered_tag_analysis:
                filtered_tag_analysis[role_category] = []
            filtered_tag_analysis[role_category].append({
                'TagName': row['TagName'],
                'ResponseCount': row['ResponseCount']
            })
        
        analytics_data['filtered_tag_analysis'] = filtered_tag_analysis
        
        # Tag-Role distribution analysis using effective tags (reverse of filtered_tag_analysis)
        tag_role_query = """
        WITH EffectiveResponseTags AS (
            -- Original tags
            SELECT bt.TagID, bt.ResponseID
            FROM BridgeResponseTags bt
            
            UNION
            
            -- Manual additions
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE mto.Action = 'ADD'
            
            EXCEPT
            
            -- Manual removals
            SELECT mto.TagID, f.ResponseID
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.SurveyResponseNumber = f.SurveyResponseNumber 
                AND mto.QuestionID = f.QuestionID
            WHERE mto.Action = 'REMOVE'
        )
        SELECT 
            t.TagName,
            r.RoleCategory,
            COUNT(ert.ResponseID) as ResponseCount
        FROM FactSurveyResponses f
        JOIN DimRole r ON f.RoleID = r.RoleID
        JOIN EffectiveResponseTags ert ON f.ResponseID = ert.ResponseID
        JOIN DimTags t ON ert.TagID = t.TagID
        WHERE t.IsActive = 1
        GROUP BY t.TagName, r.RoleCategory
        ORDER BY t.TagName, ResponseCount DESC
        """
        tag_roles = conn.execute(tag_role_query).fetchall()
        
        # Organize role distribution by tag
        tag_role_distribution = {}
        for row in tag_roles:
            tag_name = row['TagName']
            if tag_name not in tag_role_distribution:
                tag_role_distribution[tag_name] = []
            tag_role_distribution[tag_name].append({
                'RoleCategory': row['RoleCategory'],
                'ResponseCount': row['ResponseCount']
            })
        
        analytics_data['tag_role_distribution'] = tag_role_distribution
        
        conn.close()
        return jsonify(analytics_data)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/response/<int:response_id>/tags', methods=['GET'])
def get_effective_tags(response_id):
    """Get effective tags for a response (original + manual overrides)"""
    try:
        conn = get_db_connection()
        
        # Get response details for stable identifiers
        response_query = """
        SELECT SurveyResponseNumber, QuestionID 
        FROM FactSurveyResponses 
        WHERE ResponseID = ?
        """
        response_info = conn.execute(response_query, (response_id,)).fetchone()
        
        if not response_info:
            conn.close()
            return jsonify({"error": "Response not found"}), 404
            
        # Get effective tags with override logic
        effective_tags_query = """
        WITH OriginalTags AS (
            -- Start with original tags from algorithm
            SELECT bt.TagID, 'ORIGINAL' as Source
            FROM BridgeResponseTags bt
            WHERE bt.ResponseID = ?
        ),
        LatestOverrides AS (
            -- Get the most recent action for each tag (in case of multiple overrides)
            SELECT TagID, Action, ROW_NUMBER() OVER (PARTITION BY TagID ORDER BY AppliedDate DESC) as rn
            FROM ManualTagOverrides mto
            WHERE mto.SurveyResponseNumber = ? 
            AND mto.QuestionID = ?
        ),
        CurrentOverrides AS (
            -- Only keep the latest action for each tag
            SELECT TagID, Action
            FROM LatestOverrides
            WHERE rn = 1
        ),
        FinalTags AS (
            -- Apply override logic: 
            -- 1. Include original tags that have no override or have ADD override
            -- 2. Include manually added tags (tags not in original but have ADD override)
            SELECT 
                ot.TagID, 
                CASE WHEN co.Action = 'ADD' THEN 'MANUAL_ADD' ELSE ot.Source END as Source
            FROM OriginalTags ot
            LEFT JOIN CurrentOverrides co ON ot.TagID = co.TagID
            WHERE co.Action IS NULL OR co.Action = 'ADD'
            
            UNION
            
            -- Include tags that are manually added but were never original
            SELECT co.TagID, 'MANUAL_ADD' as Source
            FROM CurrentOverrides co
            WHERE co.Action = 'ADD' 
            AND co.TagID NOT IN (SELECT TagID FROM OriginalTags)
        )
        SELECT DISTINCT 
            ft.TagID,
            dt.TagName,
            dt.TagCategory,
            dt.TagDescription,
            ft.Source,
            CASE WHEN ft.Source = 'MANUAL_ADD' THEN 1 ELSE 0 END as IsManuallyAdded,
            0 as IsManuallyRemoved
        FROM FinalTags ft
        JOIN DimTags dt ON ft.TagID = dt.TagID
        WHERE dt.IsActive = 1
        ORDER BY dt.TagName
        """
        
        tags = conn.execute(effective_tags_query, (
            response_id,
            response_info['SurveyResponseNumber'], response_info['QuestionID']
        )).fetchall()
        
        conn.close()
        return jsonify([dict(tag) for tag in tags])
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/response/<int:response_id>/tags', methods=['POST'])
def modify_response_tags(response_id):
    """Add or remove tags from a response"""
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        action = data.get('action')  # 'ADD' or 'REMOVE'
        applied_by = data.get('applied_by', 'System')
        notes = data.get('notes', '')
        
        if not all([tag_id, action]) or action not in ['ADD', 'REMOVE']:
            return jsonify({"error": "Invalid request. Need tag_id and action (ADD/REMOVE)"}), 400
            
        conn = get_db_connection()
        
        # Get response details for stable identifiers
        response_query = """
        SELECT SurveyResponseNumber, QuestionID 
        FROM FactSurveyResponses 
        WHERE ResponseID = ?
        """
        response_info = conn.execute(response_query, (response_id,)).fetchone()
        
        if not response_info:
            conn.close()
            return jsonify({"error": "Response not found"}), 404
            
        # Insert the override (will replace if same key exists due to PRIMARY KEY)
        from datetime import datetime
        override_query = """
        INSERT OR REPLACE INTO ManualTagOverrides 
        (SurveyResponseNumber, QuestionID, TagID, Action, AppliedBy, AppliedDate, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        conn.execute(override_query, (
            response_info['SurveyResponseNumber'],
            response_info['QuestionID'],
            tag_id,
            action,
            applied_by,
            datetime.now().isoformat(),
            notes
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"Tag {action.lower()}ed successfully"})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags/available', methods=['GET'])
def get_available_tags():
    """Get all available tags for the tag editor"""
    try:
        conn = get_db_connection()
        
        query = """
        SELECT TagID, TagName, TagCategory, TagDescription
        FROM DimTags 
        WHERE IsActive = 1
        ORDER BY TagCategory, TagName
        """
        
        tags = conn.execute(query).fetchall()
        conn.close()
        
        return jsonify([dict(tag) for tag in tags])
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/overrides/stats', methods=['GET'])
def get_override_stats():
    """Get statistics about manual tag overrides"""
    try:
        conn = get_db_connection()
        
        stats_query = """
        SELECT 
            COUNT(*) as total_overrides,
            COUNT(CASE WHEN Action = 'ADD' THEN 1 END) as additions,
            COUNT(CASE WHEN Action = 'REMOVE' THEN 1 END) as removals,
            COUNT(DISTINCT SurveyResponseNumber || '-' || QuestionID) as responses_modified,
            COUNT(DISTINCT AppliedBy) as editors,
            COUNT(DISTINCT TagID) as unique_tags_modified
        FROM ManualTagOverrides
        """
        
        stats = conn.execute(stats_query).fetchone()
        conn.close()
        
        return jsonify(dict(stats))
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/response/<int:response_id>/highlight', methods=['GET'])
def get_response_highlights(response_id):
    """Get text highlighting data for a response based on tagging keywords"""
    try:
        conn = get_db_connection()
        
        # Get response text and current tags
        response_query = """
        SELECT f.ResponseText
        FROM FactSurveyResponses f
        WHERE f.ResponseID = ?
        """
        response_result = conn.execute(response_query, (response_id,)).fetchone()
        
        if not response_result:
            conn.close()
            return jsonify({"error": "Response not found"}), 404
            
        response_text = response_result['ResponseText']
        
        # Get current effective tags for this response using the same logic
        response_info_query = """
        SELECT SurveyResponseNumber, QuestionID 
        FROM FactSurveyResponses 
        WHERE ResponseID = ?
        """
        response_info = conn.execute(response_info_query, (response_id,)).fetchone()
        
        if not response_info:
            conn.close()
            return jsonify({"error": "Response info not found"}), 404
            
        # Get effective tags with override logic
        effective_tags_query = """
        WITH OriginalTags AS (
            -- Start with original tags from algorithm
            SELECT bt.TagID
            FROM BridgeResponseTags bt
            WHERE bt.ResponseID = ?
        ),
        LatestOverrides AS (
            -- Get the most recent action for each tag (in case of multiple overrides)
            SELECT TagID, Action, ROW_NUMBER() OVER (PARTITION BY TagID ORDER BY AppliedDate DESC) as rn
            FROM ManualTagOverrides mto
            WHERE mto.SurveyResponseNumber = ? 
            AND mto.QuestionID = ?
        ),
        CurrentOverrides AS (
            -- Only keep the latest action for each tag
            SELECT TagID, Action
            FROM LatestOverrides
            WHERE rn = 1
        ),
        FinalTags AS (
            -- Apply override logic: 
            -- 1. Include original tags that have no override or have ADD override
            -- 2. Include manually added tags (tags not in original but have ADD override)
            SELECT ot.TagID
            FROM OriginalTags ot
            LEFT JOIN CurrentOverrides co ON ot.TagID = co.TagID
            WHERE co.Action IS NULL OR co.Action = 'ADD'
            
            UNION
            
            -- Include tags that are manually added but were never original
            SELECT co.TagID
            FROM CurrentOverrides co
            WHERE co.Action = 'ADD' 
            AND co.TagID NOT IN (SELECT TagID FROM OriginalTags)
        )
        SELECT DISTINCT 
            ft.TagID,
            dt.TagName,
            dt.TagCategory,
            dt.TagDescription
        FROM FinalTags ft
        JOIN DimTags dt ON ft.TagID = dt.TagID
        WHERE dt.IsActive = 1
        ORDER BY dt.TagName
        """
        
        effective_tags = conn.execute(effective_tags_query, (
            response_id,
            response_info['SurveyResponseNumber'], response_info['QuestionID']
        )).fetchall()
        
        effective_tags = [dict(tag) for tag in effective_tags]
        
        # Define the same keyword mapping as in your Python tagging algorithm
        tag_keywords = {
            'Compensation & Incentives': {
                'primary': ['compensation', 'salary', 'pay', 'wage', 'bonus', 'incentive', 'sign on bonus'],
                'secondary': ['financial incentive', 'tuition assistance', 'student loan', 'pay well', 'no money', 'paying student loans', 'loan forgiveness'],
                'context': ['competitive', 'higher', 'financial', 'money']
            },
            'Behavioral Health Need': {
                'primary': ['behavioral health', 'mental health', 'psychology', 'psychiatry', 'psychiatric care', 'psychiatric'],
                'secondary': ['counseling', 'therapy', 'trauma', 'addiction', 'psych eval', 'mental health services'],
                'context': ['services', 'treatment', 'support', 'care', 'patients']
            },
            'Burnout & Wellbeing': {
                'primary': ['burnout', 'burn out', 'wellbeing', 'wellness', 'work-life balance', 'work life balance'],
                'secondary': ['stress', 'exhaustion', 'fatigue', 'self-care', 'worn down', 'wears down', 'overworked', 'dissatisfaction'],
                'context': ['management', 'prevention', 'support', 'balance', 'employees']
            },
            'Funding & Grants': {
                'primary': ['funding', 'grant', 'budget'],
                'secondary': ['financial support', 'resources to pay', 'tuition reimbursement', 'tuition assistance'],
                'context': ['federal', 'state', 'apply', 'seek']
            },
            'Leadership Development': {
                'primary': ['leadership development', 'leadership training', 'management training', 'supervision', 'leadership tracks'],
                'secondary': ['leadership', 'management', 'supervisor training', 'executive', 'supervision skills', 'leaders'],
                'context': ['skills', 'program', 'course', 'promotion', 'training at each level']
            },
            'Licensing & Scope': {
                'primary': ['license', 'licensing', 'scope of practice', 'certification'],
                'secondary': ['credential', 'accreditation', 'board certified'],
                'context': ['requirements', 'maintain', 'renew']
            },
            'Childcare Support': {
                'primary': ['childcare', 'child care', 'daycare'],
                'secondary': ['family support', 'dependent care'],
                'context': ['benefits', 'assistance', 'services']
            },
            'Housing & Transportation': {
                'primary': ['housing', 'transportation', 'affordable housing'],
                'secondary': ['commute', 'travel', 'relocation', 'finding housing'],
                'context': ['assistance', 'support', 'stipend', 'crisis', 'help with']
            },
            'Workforce Challenges': {
                'primary': ['shortage', 'understaffed', 'short staffed', 'staffing shortage', 'gaping hole', 'lack of', 'not enough', 'scarce', 'vacant', 'hard to hire', 'difficult to hire', 'recruitment', 'recruiting', 'hire', 'hiring', 'attract'],
                'secondary': ['turnover', 'high turnover', 'leaving', 'staff leaving', 'people leaving', 'contract staff', 'temp workers', 'agency staff', 'retention', 'empty positions', 'open positions', 'need more', 'need staff'],
                'context': ['workforce', 'positions', 'roles', 'employees', 'staff', 'workers', 'hiring', 'recruitment', 'talent', 'personnel', 'challenges']
            },
            'Training & Development': {
                'primary': ['professional development', 'continuing education', 'cme', 'continuing ed', 'residency', 'fellowship', 'medical school', 'terminology', 'simulation', 'sim lab', 'simulation training', 'technology training', 'tech training'],
                'secondary': ['career development', 'skill development', 'conferences', 'educators', 'university', 'academic', 'rotation', 'hands-on training', 'skills lab', 'practice lab', 'emr training', 'software training'],
                'context': ['opportunities', 'program', 'support', 'grow', 'introduced', 'training', 'education', 'practice', 'lab', 'computer', 'digital', 'electronic']
            },
            'Clinical Services': {
                'primary': ['specialist', 'specialty care', 'subspecialty', 'primary care', 'family medicine', 'family physician', 'primary care physician', 'interdisciplinary', 'multidisciplinary', 'team-based care'],
                'secondary': ['specialized', 'quaternary care', 'general practice', 'family doctor', 'pcp', 'collaborative care', 'care coordination'],
                'context': ['referral', 'specialized', 'advanced', 'preventive', 'routine', 'general', 'team', 'collaboration', 'coordination']
            },
            'Clinical Competency': {
                'primary': ['clinical competency', 'clinical skills', 'patient care skills'],
                'secondary': ['bedside manner', 'clinical training'],
                'context': ['evidence-based', 'best practices', 'quality']
            },
            'Quality & Safety': {
                'primary': ['quality improvement', 'patient safety', 'quality assurance'],
                'secondary': ['outcomes', 'safety', 'quality'],
                'context': ['improvement', 'measures', 'initiatives']
            },
            'Rural Care': {
                'primary': ['rural health', 'rural care', 'rural hospital', 'rural community'],
                'secondary': ['rural areas', 'rural', 'geographic locations in rural'],
                'context': ['remote', 'isolated', 'distance']
            },
            'Allied Health': {
                'primary': ['social worker', 'social workers', 'patient navigator', 'patient navigators'],
                'secondary': ['laboratory technician', 'lab tech', 'respiratory therapist', 'rad tech', 'dietitian', 'physical therapist', 'occupational therapist', 'allied health'],
                'context': ['technician', 'therapist', 'navigator', 'support staff']
            }
        }
        
        # Find matching keywords for each effective tag
        highlights = []
        text_lower = response_text.lower()
        
        for tag in effective_tags:
            tag_name = tag['TagName']
            if tag_name in tag_keywords:
                keywords = tag_keywords[tag_name]
                
                # Check all keyword types
                for keyword_type in ['primary', 'secondary', 'context']:
                    if keyword_type in keywords:
                        for keyword in keywords[keyword_type]:
                            if keyword in text_lower:
                                # Find the exact position in the original text
                                start_idx = text_lower.find(keyword)
                                while start_idx != -1:
                                    highlights.append({
                                        'keyword': keyword,
                                        'tag_name': tag_name,
                                        'tag_category': tag['TagCategory'],
                                        'start': start_idx,
                                        'end': start_idx + len(keyword),
                                        'type': keyword_type,
                                        'score': 3 if keyword_type == 'primary' else 2 if keyword_type == 'secondary' else 1
                                    })
                                    start_idx = text_lower.find(keyword, start_idx + 1)
        
        # Sort highlights by position
        highlights.sort(key=lambda x: x['start'])
        
        conn.close()
        return jsonify({
            'response_text': response_text,
            'highlights': highlights,
            'tags': effective_tags
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
