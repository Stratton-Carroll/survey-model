from flask import Flask, jsonify
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
        
        # Get tags with response counts
        query = """
        SELECT t.TagID, t.TagKey, t.TagName, t.TagCategory, t.TagPriority, 
               t.TagDescription, t.IsActive, COUNT(bt.ResponseID) as ResponseCount 
        FROM DimTags t 
        LEFT JOIN BridgeResponseTags bt ON t.TagID = bt.TagID 
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
        SELECT 
            dt.TagID,
            dt.TagName,
            dt.TagCategory,
            COUNT(DISTINCT brt.ResponseID) as TagCount
        FROM FactSurveyResponses fsr
        JOIN BridgeResponseTags brt ON fsr.ResponseID = brt.ResponseID
        JOIN DimTags dt ON brt.TagID = dt.TagID
        WHERE fsr.QuestionID = ?
        GROUP BY dt.TagID, dt.TagName, dt.TagCategory
        ORDER BY TagCount DESC
        """
        tag_distribution = conn.execute(query, (question_id,)).fetchall()
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
        
        # For each response, get all its tags
        response_list = []
        for response in responses:
            # Get all tags for this response
            tags_query = """
            SELECT t.TagID, t.TagName, t.TagCategory
            FROM BridgeResponseTags bt
            JOIN DimTags t ON bt.TagID = t.TagID
            WHERE bt.ResponseID = ? AND t.IsActive = 1
            ORDER BY t.TagName
            """
            tags = conn.execute(tags_query, (response['ResponseID'],)).fetchall()
            
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
        
        # Get all responses with their associated tags
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
            r.RoleStandardized as RoleName,
            GROUP_CONCAT(t.TagName, '|') as TagNames,
            GROUP_CONCAT(t.TagCategory, '|') as TagCategories,
            GROUP_CONCAT(t.TagID, '|') as TagIDs
        FROM FactSurveyResponses f
        JOIN DimQuestion q ON f.QuestionID = q.QuestionID
        LEFT JOIN DimOrganization o ON f.OrganizationID = o.OrganizationID
        LEFT JOIN DimGeography g ON f.GeographyID = g.GeographyID
        LEFT JOIN DimRole r ON f.RoleID = r.RoleID
        LEFT JOIN BridgeResponseTags bt ON f.ResponseID = bt.ResponseID
        LEFT JOIN DimTags t ON bt.TagID = t.TagID AND t.IsActive = 1
        WHERE f.HasResponse = 1 AND f.ResponseText IS NOT NULL AND f.ResponseText != ''
        GROUP BY f.ResponseID, f.SurveyResponseNumber, f.ResponseText, q.QuestionID, q.QuestionText, q.QuestionShort, o.OrganizationName, o.OrganizationType, g.PrimaryCounty, g.State, r.RoleStandardized
        ORDER BY q.QuestionID, f.SurveyResponseNumber
        """
        
        responses = conn.execute(query).fetchall()
        conn.close()
        
        # Process the results to create a nested structure
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
            
            # Parse tags
            tags = []
            if response['TagNames']:
                tag_names = response['TagNames'].split('|')
                tag_categories = response['TagCategories'].split('|') if response['TagCategories'] else []
                tag_ids = response['TagIDs'].split('|') if response['TagIDs'] else []
                
                for i, name in enumerate(tag_names):
                    if name:  # Skip empty names
                        tags.append({
                            'TagID': tag_ids[i] if i < len(tag_ids) else None,
                            'TagName': name,
                            'TagCategory': tag_categories[i] if i < len(tag_categories) else None
                        })
            
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
        
        # Priority areas (top tags by response count)
        priority_areas_query = """
        SELECT t.TagID, t.TagName, t.TagDescription, t.TagCategory, COUNT(bt.ResponseID) as ResponseCount
        FROM DimTags t
        LEFT JOIN BridgeResponseTags bt ON t.TagID = bt.TagID
        WHERE t.IsActive = 1
        GROUP BY t.TagID, t.TagName, t.TagDescription, t.TagCategory
        ORDER BY ResponseCount DESC
        LIMIT 10
        """
        priority_areas = conn.execute(priority_areas_query).fetchall()
        analytics_data['priority_areas'] = [dict(row) for row in priority_areas]
        
        # Filtered tag analysis by role category
        filtered_tag_query = """
        SELECT 
            r.RoleCategory,
            t.TagName,
            COUNT(bt.ResponseID) as ResponseCount
        FROM FactSurveyResponses f
        JOIN DimRole r ON f.RoleID = r.RoleID
        JOIN BridgeResponseTags bt ON f.ResponseID = bt.ResponseID
        JOIN DimTags t ON bt.TagID = t.TagID
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
        
        # Tag-Role distribution analysis (reverse of filtered_tag_analysis)
        tag_role_query = """
        SELECT 
            t.TagName,
            r.RoleCategory,
            COUNT(bt.ResponseID) as ResponseCount
        FROM FactSurveyResponses f
        JOIN DimRole r ON f.RoleID = r.RoleID
        JOIN BridgeResponseTags bt ON f.ResponseID = bt.ResponseID
        JOIN DimTags t ON bt.TagID = t.TagID
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

if __name__ == '__main__':
    app.run(debug=True)
