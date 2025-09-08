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
        
        # Get tags with effective response counts (3-layer system: Algorithmic -> Question -> Manual)
        query = """
        WITH AllResponseTags AS (
            -- All unique Response-Tag combinations from all layers
            SELECT DISTINCT ResponseID, TagID FROM (
                -- Layer 1: Original algorithmic tags
                SELECT bt.ResponseID, bt.TagID FROM BridgeResponseTags bt
                UNION ALL
                -- Layer 2: Question-based mappings  
                SELECT qtm.ResponseID, qtm.TagID FROM QuestionTagMappings qtm WHERE qtm.IsActive = 1
                UNION ALL
                -- Layer 3: Manual additions
                SELECT mto.ResponseID, mto.TagID FROM ManualTagOverrides mto WHERE mto.Action = 'ADD' AND mto.IsActive = 1
            )
        ),
        ManualRemovals AS (
            -- Get manual removals to subtract
            SELECT mto.ResponseID, mto.TagID 
            FROM ManualTagOverrides mto 
            WHERE mto.Action = 'REMOVE' AND mto.IsActive = 1
        ),
        EffectiveResponseTags AS (
            -- Final effective tags (all additions minus removals)
            SELECT art.ResponseID, art.TagID 
            FROM AllResponseTags art
            LEFT JOIN ManualRemovals mr ON art.ResponseID = mr.ResponseID AND art.TagID = mr.TagID
            WHERE mr.TagID IS NULL
        )
        SELECT t.TagID, t.TagKey, t.TagName, t.TagCategory, t.TagPriority, 
               t.TagDescription, t.IsActive, t.TagLevel, t.ParentTagID,
               COUNT(DISTINCT ert.ResponseID) as ResponseCount,
               CASE WHEN t.TagLevel = 1 THEN t.TagName 
                    ELSE (SELECT p.TagName FROM DimTags p WHERE p.TagID = t.ParentTagID) 
               END as PrimaryTagName
        FROM DimTags t 
        LEFT JOIN EffectiveResponseTags ert ON t.TagID = ert.TagID 
        WHERE t.IsActive = 1
        GROUP BY t.TagID, t.TagKey, t.TagName, t.TagCategory, t.TagPriority, t.TagDescription, t.IsActive, t.TagLevel, t.ParentTagID
        ORDER BY ResponseCount DESC, t.TagLevel, t.TagName
        """
        
        tags = conn.execute(query).fetchall()
        conn.close()
        return jsonify([dict(tag) for tag in tags])
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/sankey', methods=['GET'])
def get_sankey_data():
    """Generate Sankey diagram data from effective tags.

    - Select top 10 primary tags (TagLevel=1) by effective response count.
    - For each primary, include top N sub-tags (TagLevel=2, same parent) by count.
    - If the primary has no sub-tags (or remainder), add an 'Other' bucket so every
      primary has at least one outgoing link. This ensures ranks #1..#10 always show.
    """
    try:
        conn = get_db_connection()

        # Build effective tags set (original + question mappings + manual adds - removals)
        effective_cte = """
        WITH AllResponseTags AS (
            SELECT DISTINCT ResponseID, TagID FROM (
                SELECT bt.ResponseID, bt.TagID FROM BridgeResponseTags bt
                UNION ALL
                SELECT qtm.ResponseID, qtm.TagID FROM QuestionTagMappings qtm WHERE qtm.IsActive = 1
                UNION ALL
                SELECT mto.ResponseID, mto.TagID FROM ManualTagOverrides mto WHERE mto.Action = 'ADD' AND mto.IsActive = 1
            )
        ),
        ManualRemovals AS (
            SELECT mto.ResponseID, mto.TagID 
            FROM ManualTagOverrides mto 
            WHERE mto.Action = 'REMOVE' AND mto.IsActive = 1
        ),
        EffectiveResponseTags AS (
            SELECT art.ResponseID, art.TagID 
            FROM AllResponseTags art
            LEFT JOIN ManualRemovals mr ON art.ResponseID = mr.ResponseID AND art.TagID = mr.TagID
            WHERE mr.TagID IS NULL
        )
        """

        # Top 5 primary tags by effective response count (clean focus)
        primary_query = f"""
        {effective_cte}
        SELECT dt.TagID, dt.TagName, dt.TagCategory,
               COUNT(DISTINCT ert.ResponseID) AS ResponseCount
        FROM DimTags dt
        LEFT JOIN EffectiveResponseTags ert ON dt.TagID = ert.TagID
        WHERE dt.IsActive = 1 AND dt.TagLevel = 1
        GROUP BY dt.TagID, dt.TagName, dt.TagCategory
        ORDER BY ResponseCount DESC
        LIMIT 5
        """
        prim_rows = conn.execute(primary_query).fetchall()
        primaries = [dict(r) for r in prim_rows]

        if not primaries:
            conn.close()
            return jsonify({
                'nodes': {'labels': [], 'colors': [], 'hovers': []},
                'links': {'source': [], 'target': [], 'value': [], 'colors': [], 'hovers': []}
            })

        primary_ids = [p['TagID'] for p in primaries]

        # Sub-tag counts for those primaries
        placeholders = ','.join(['?'] * len(primary_ids))
        sub_query = f"""
        {effective_cte}
        SELECT dt.ParentTagID AS PrimaryTagID,
               dt.TagID,
               dt.TagName,
               COUNT(DISTINCT ert.ResponseID) AS ResponseCount
        FROM DimTags dt
        LEFT JOIN EffectiveResponseTags ert ON dt.TagID = ert.TagID
        WHERE dt.IsActive = 1 AND dt.TagLevel = 2 AND dt.ParentTagID IN ({placeholders})
        GROUP BY dt.ParentTagID, dt.TagID, dt.TagName
        ORDER BY dt.ParentTagID, ResponseCount DESC
        """
        sub_rows = conn.execute(sub_query, primary_ids).fetchall()
        conn.close()

        # Organize sub-tags by parent
        subs_by_parent = {}
        for r in sub_rows:
            d = dict(r)
            subs_by_parent.setdefault(d['PrimaryTagID'], []).append(d)

        # Theme-consistent color palette for 10 ranks
        primary_palette = ['#7a9944', '#ea580c', '#0891b2', '#059669', '#7c3aed',
                           '#dc2626', '#f59e0b', '#8b5cf6', '#06b6d4', '#64748b']

        def hex_to_rgba(hex_color, alpha):
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"

        # Build nodes and links
        labels = []
        node_colors = []
        node_hovers = []
        node_x = []
        node_y = []
        links_source = []
        links_target = []
        links_value = []
        link_colors = []
        link_hovers = []

        node_index = {}
        next_index = 0

        # Add primaries with rank-based labels (use circled numerals for clarity)
        circled = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩']
        for rank, p in enumerate(primaries, start=1):
            label = f"{circled[rank-1]} {p['TagName']}"
            color = primary_palette[(rank - 1) % len(primary_palette)]
            hover = f"{p['TagName']} — {p['ResponseCount']} mentions"
            node_index[p['TagID']] = next_index
            labels.append(label)
            node_colors.append(color)
            node_hovers.append(hover)
            node_x.append(0.03)
            # Even vertical spacing for left nodes with margins
            if len(primaries) > 1:
                y_val = 0.06 + (rank - 1) * (0.88 / (len(primaries) - 1))
            else:
                y_val = 0.5
            node_y.append(y_val)
            next_index += 1

        # For each primary, add top sub-tags (max 5). No 'Other' bucket.
        # First select the sub-tags we plan to render so we can space them globally.
        MAX_SUBS = 5
        chosen_by_parent = []  # list of tuples (p_rank, p_dict, p_idx, p_color, [sub_dicts])
        for rank, p in enumerate(primaries, start=1):
            p_id = p['TagID']
            p_idx = node_index[p_id]
            p_color = primary_palette[(rank - 1) % len(primary_palette)]
            subs = subs_by_parent.get(p_id, [])
            chosen = subs[:MAX_SUBS]
            chosen_by_parent.append((rank, p, p_idx, p_color, chosen))

        # Compute global vertical positions for all right-side nodes to prevent overlap
        total_right = sum(len(item[4]) for item in chosen_by_parent)
        def y_for_right(i, N):
            if N <= 1:
                return 0.5
            # Use 0.04..0.96 to give label breathing room at edges
            return 0.04 + i * (0.92 / (N - 1))

        right_counter = 0
        for rank, p, p_idx, p_color, chosen in chosen_by_parent:
            for s in chosen:
                s_idx = next_index
                next_index += 1
                labels.append(s['TagName'])
                node_colors.append(hex_to_rgba(p_color, 0.72))
                node_hovers.append(f"{s['TagName']} — {s['ResponseCount']} mentions")
                node_x.append(0.92)
                y_val = y_for_right(right_counter, total_right)
                node_y.append(y_val)
                links_source.append(p_idx)
                links_target.append(s_idx)
                links_value.append(int(s['ResponseCount'] or 0))
                link_colors.append(hex_to_rgba(p_color, 0.32))
                link_hovers.append(f"{p['TagName']} → {s['TagName']}: {int(s['ResponseCount'] or 0)}")
                right_counter += 1

        return jsonify({
            'nodes': {
                'labels': labels,
                'colors': node_colors,
                'hovers': node_hovers,
                'x': node_x,
                'y': node_y,
                'leftCount': len(primaries),
                'rightCount': total_right
            },
            'links': {
                'source': links_source,
                'target': links_target,
                'value': links_value,
                'colors': link_colors,
                'hovers': link_hovers
            }
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/questions/<int:question_id>/tag-distribution', methods=['GET'])
def get_question_tag_distribution(question_id):
    try:
        conn = get_db_connection()
        query = """
        WITH AllQuestionResponseTags AS (
            -- All Response-Tag combinations for this question from all layers
            SELECT DISTINCT f.ResponseID, TagID FROM (
                -- Layer 1: Original algorithmic tags
                SELECT bt.ResponseID, bt.TagID FROM BridgeResponseTags bt
                JOIN FactSurveyResponses f ON bt.ResponseID = f.ResponseID
                WHERE f.QuestionID = ?
                UNION ALL
                -- Layer 2: Question-based mappings
                SELECT qtm.ResponseID, qtm.TagID FROM QuestionTagMappings qtm
                JOIN FactSurveyResponses f ON qtm.ResponseID = f.ResponseID  
                WHERE f.QuestionID = ? AND qtm.IsActive = 1
                UNION ALL
                -- Layer 3: Manual additions
                SELECT mto.ResponseID, mto.TagID FROM ManualTagOverrides mto
                JOIN FactSurveyResponses f ON mto.ResponseID = f.ResponseID
                WHERE f.QuestionID = ? AND mto.Action = 'ADD' AND mto.IsActive = 1
            ) all_tags
            JOIN FactSurveyResponses f ON all_tags.ResponseID = f.ResponseID
            WHERE f.QuestionID = ?
        ),
        ManualRemovals AS (
            -- Manual removals for this question
            SELECT mto.ResponseID, mto.TagID 
            FROM ManualTagOverrides mto
            JOIN FactSurveyResponses f ON mto.ResponseID = f.ResponseID
            WHERE f.QuestionID = ? AND mto.Action = 'REMOVE' AND mto.IsActive = 1
        ),
        EffectiveResponseTags AS (
            -- Final effective tags (additions minus removals)
            SELECT aqrt.ResponseID, aqrt.TagID 
            FROM AllQuestionResponseTags aqrt
            LEFT JOIN ManualRemovals mr ON aqrt.ResponseID = mr.ResponseID AND aqrt.TagID = mr.TagID
            WHERE mr.TagID IS NULL
        )
        SELECT 
            dt.TagID,
            dt.TagName,
            dt.TagCategory,
            dt.TagLevel,
            dt.ParentTagID,
            COUNT(DISTINCT ert.ResponseID) as TagCount
        FROM EffectiveResponseTags ert
        JOIN DimTags dt ON ert.TagID = dt.TagID
        WHERE dt.IsActive = 1
        GROUP BY dt.TagID, dt.TagName, dt.TagCategory, dt.TagLevel, dt.ParentTagID
        ORDER BY TagCount DESC, dt.TagLevel, dt.TagName
        """
        tag_distribution = conn.execute(query, (question_id, question_id, question_id, question_id, question_id)).fetchall()
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
            
            # Get effective tags using 3-layer priority system: Algorithmic -> Question Mappings -> Manual Overrides
            effective_tags_query = """
            WITH LatestManualOverrides AS (
                -- Get the latest manual override action for each tag
                SELECT 
                    mto.TagID,
                    mto.Action,
                    ROW_NUMBER() OVER (PARTITION BY mto.TagID ORDER BY mto.AppliedDate DESC) as rn
                FROM ManualTagOverrides mto
                WHERE mto.ResponseID = ? AND mto.IsActive = 1
            ),
            AllTagSources AS (
                -- Layer 1: Original algorithmic tags (not manually removed)
                SELECT bt.TagID, 'algorithmic' as Source, 0 as Priority
                FROM BridgeResponseTags bt
                LEFT JOIN LatestManualOverrides lmo ON bt.TagID = lmo.TagID AND lmo.rn = 1
                WHERE bt.ResponseID = ? AND (lmo.Action IS NULL OR lmo.Action != 'REMOVE')
                
                UNION ALL
                
                -- Layer 2: Question-based tag mappings (not manually removed)
                SELECT qtm.TagID, 'question-mapping' as Source, 1 as Priority
                FROM QuestionTagMappings qtm
                LEFT JOIN LatestManualOverrides lmo ON qtm.TagID = lmo.TagID AND lmo.rn = 1
                WHERE qtm.ResponseID = ? AND qtm.IsActive = 1 
                      AND (lmo.Action IS NULL OR lmo.Action != 'REMOVE')
                
                UNION ALL
                
                -- Layer 3: Manual additions (highest priority)
                SELECT lmo.TagID, 'manual' as Source, 2 as Priority
                FROM LatestManualOverrides lmo
                WHERE lmo.rn = 1 AND lmo.Action = 'ADD'
            ),
            EffectiveTags AS (
                -- Get highest priority source for each tag
                SELECT 
                    TagID,
                    Source,
                    ROW_NUMBER() OVER (PARTITION BY TagID ORDER BY Priority DESC) as rn
                FROM AllTagSources
            )
            SELECT DISTINCT 
                et.TagID, 
                t.TagName, 
                t.TagCategory, 
                t.TagLevel,
                t.ParentTagID,
                et.Source,
                CASE WHEN et.Source = 'manual' THEN 1 ELSE 0 END as IsManuallyAdded,
                CASE WHEN t.TagLevel = 1 THEN t.TagName 
                     ELSE (SELECT p.TagName FROM DimTags p WHERE p.TagID = t.ParentTagID) 
                END as PrimaryTagName
            FROM EffectiveTags et
            JOIN DimTags t ON et.TagID = t.TagID
            WHERE t.IsActive = 1 AND et.rn = 1
            ORDER BY t.TagLevel, t.TagName
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
        
        # Overview metrics (dynamic counts)
        overview_query = """
        SELECT 
            COUNT(CASE WHEN f.HasResponse = 1 THEN 1 END) as total_responses,
            COUNT(DISTINCT f.SurveyResponseNumber) as unique_respondents,
            (SELECT COUNT(*) FROM DimQuestion) as total_questions,
            COUNT(DISTINCT CASE WHEN f.OrganizationID IS NOT NULL THEN f.OrganizationID END) as organizations,
            AVG(CAST(q.ResponseRate AS REAL)) as avg_response_rate,
            AVG(CASE WHEN f.HasResponse = 1 THEN f.WordCount END) as avg_word_count,
            AVG(CASE WHEN f.HasResponse = 1 THEN f.ResponseLength END) as avg_response_length
        FROM FactSurveyResponses f
        LEFT JOIN DimQuestion q ON f.QuestionID = q.QuestionID
        """
        overview = conn.execute(overview_query).fetchone()
        analytics_data['overview'] = dict(overview)
        
        # Role category analysis (existing)
        role_category_query = """
        SELECT r.RoleCategory, COUNT(*) as response_count
        FROM FactSurveyResponses f
        JOIN DimRole r ON f.RoleID = r.RoleID
        WHERE f.HasResponse = 1
        GROUP BY r.RoleCategory
        ORDER BY response_count DESC
        """
        role_categories = conn.execute(role_category_query).fetchall()
        analytics_data['role_category_analysis'] = [dict(row) for row in role_categories]

        # Role type analysis (new)
        role_type_query = """
        SELECT r.RoleType, COUNT(*) as response_count
        FROM FactSurveyResponses f
        JOIN DimRole r ON f.RoleID = r.RoleID
        WHERE f.HasResponse = 1
        GROUP BY r.RoleType
        ORDER BY response_count DESC
        """
        role_types = conn.execute(role_type_query).fetchall()
        analytics_data['role_type_analysis'] = [dict(row) for row in role_types]
        
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
        WHERE t.IsActive = 1 AND t.TagLevel = 1
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

        # Filtered tag analysis by role type (new)
        filtered_tag_role_type_query = """
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
            r.RoleType,
            t.TagName,
            COUNT(ert.ResponseID) as ResponseCount
        FROM FactSurveyResponses f
        JOIN DimRole r ON f.RoleID = r.RoleID
        JOIN EffectiveResponseTags ert ON f.ResponseID = ert.ResponseID
        JOIN DimTags t ON ert.TagID = t.TagID
        WHERE t.IsActive = 1
        GROUP BY r.RoleType, t.TagName
        ORDER BY r.RoleType, ResponseCount DESC
        """
        filtered_tags_rt = conn.execute(filtered_tag_role_type_query).fetchall()

        filtered_tag_by_role_type = {}
        for row in filtered_tags_rt:
            role_type = row['RoleType']
            if role_type not in filtered_tag_by_role_type:
                filtered_tag_by_role_type[role_type] = []
            filtered_tag_by_role_type[role_type].append({
                'TagName': row['TagName'],
                'ResponseCount': row['ResponseCount']
            })
        analytics_data['filtered_tag_by_role_type'] = filtered_tag_by_role_type
        
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
        (ResponseID, SurveyResponseNumber, QuestionID, TagID, Action, AppliedBy, AppliedDate, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        conn.execute(override_query, (
            response_id,
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

@app.route('/api/responses/<int:response_id>/effective-tags', methods=['GET'])
def get_response_effective_tags(response_id):
    """Get effective tags for a specific response with hierarchy and source information"""
    try:
        conn = get_db_connection()
        
        # Same deduplication logic as main responses endpoint
        effective_tags_query = """
        WITH LatestManualOverrides AS (
            -- Get the latest manual override action for each tag
            SELECT 
                mto.TagID,
                mto.Action,
                ROW_NUMBER() OVER (PARTITION BY mto.TagID ORDER BY mto.AppliedDate DESC) as rn
            FROM ManualTagOverrides mto
            WHERE mto.ResponseID = ? AND mto.IsActive = 1
        ),
        AllTagSources AS (
            -- Layer 1: Original algorithmic tags (not manually removed)
            SELECT bt.TagID, 'algorithmic' as Source, 0 as Priority
            FROM BridgeResponseTags bt
            LEFT JOIN LatestManualOverrides lmo ON bt.TagID = lmo.TagID AND lmo.rn = 1
            WHERE bt.ResponseID = ? AND (lmo.Action IS NULL OR lmo.Action != 'REMOVE')
            
            UNION ALL
            
            -- Layer 2: Question-based tag mappings (not manually removed)
            SELECT qtm.TagID, 'question-mapping' as Source, 1 as Priority
            FROM QuestionTagMappings qtm
            LEFT JOIN LatestManualOverrides lmo ON qtm.TagID = lmo.TagID AND lmo.rn = 1
            WHERE qtm.ResponseID = ? AND qtm.IsActive = 1 
                  AND (lmo.Action IS NULL OR lmo.Action != 'REMOVE')
            
            UNION ALL
            
            -- Layer 3: Manual additions (highest priority)
            SELECT lmo.TagID, 'manual' as Source, 2 as Priority
            FROM LatestManualOverrides lmo
            WHERE lmo.rn = 1 AND lmo.Action = 'ADD'
        ),
        EffectiveTags AS (
            -- Get highest priority source for each tag
            SELECT 
                TagID,
                Source,
                ROW_NUMBER() OVER (PARTITION BY TagID ORDER BY Priority DESC) as rn
            FROM AllTagSources
        )
        SELECT DISTINCT 
            et.TagID, 
            t.TagName, 
            t.TagCategory, 
            t.TagLevel,
            t.ParentTagID,
            et.Source,
            CASE WHEN et.Source = 'manual' THEN 1 ELSE 0 END as IsManuallyAdded,
            CASE WHEN t.TagLevel = 1 THEN t.TagName 
                 ELSE (SELECT p.TagName FROM DimTags p WHERE p.TagID = t.ParentTagID) 
            END as PrimaryTagName
        FROM EffectiveTags et
        JOIN DimTags t ON et.TagID = t.TagID
        WHERE t.IsActive = 1 AND et.rn = 1
        ORDER BY t.TagLevel, t.TagName
        """
        
        tags_result = conn.execute(effective_tags_query, (response_id, response_id, response_id)).fetchall()
        tags = [dict(tag) for tag in tags_result]
        
        conn.close()
        return jsonify(tags)
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags/available', methods=['GET'])
def get_available_tags():
    """Get all available tags for the tag editor - returns hierarchical structure"""
    try:
        conn = get_db_connection()
        
        # Get all tags with hierarchy information
        query = """
        SELECT 
            TagID, 
            TagName, 
            TagCategory, 
            TagDescription, 
            TagLevel, 
            ParentTagID,
            0 as ResponseCount
        FROM DimTags 
        WHERE IsActive = 1
        ORDER BY TagLevel, TagCategory, TagName
        """
        
        tags = conn.execute(query).fetchall()
        conn.close()
        
        # Build hierarchical structure
        primary_tags = []
        sub_tags_map = {}
        
        for tag in tags:
            tag_dict = dict(tag)
            if tag['TagLevel'] == 1:  # Primary tag
                tag_dict['SubTags'] = []
                primary_tags.append(tag_dict)
                sub_tags_map[tag['TagID']] = tag_dict['SubTags']
            else:  # Sub tag
                parent_id = tag['ParentTagID']
                if parent_id in sub_tags_map:
                    sub_tags_map[parent_id].append(tag_dict)
        
        return jsonify(primary_tags)
        
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
