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

if __name__ == '__main__':
    app.run(debug=True)
