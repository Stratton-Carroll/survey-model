"""
Individual Response Tag Analysis
Creates tags for each individual question response, not aggregated by survey
"""

import pandas as pd
import sys
import os
from collections import Counter
import re

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from healthcare_taxonomy import HEALTHCARE_CATEGORIES

def extract_key_phrases(text):
    """Extract meaningful key phrases from text"""
    if pd.isna(text) or not text or str(text).strip() == '':
        return []
    
    text_str = str(text).lower()
    
    # Define key healthcare phrases that commonly appear
    key_phrases = {
        'compensation_incentives': ['compensation', 'incentive', 'pay', 'salary', 'wage', 'bonus', 'benefit', 'tuition assistance', 'financial'],
        'behavioral_health_need': ['behavioral health', 'mental health', 'psychology', 'psychiatry', 'counseling', 'trauma', 'wellbeing'],
        'burnout_wellbeing': ['burnout', 'wellbeing', 'wellness', 'stress', 'exhaustion', 'fatigue', 'work-life balance', 'self-care'],
        'funding_grants': ['funding', 'grant', 'budget', 'financial support', 'money', 'investment', 'resources to pay'],
        'leadership_development': ['leadership', 'management', 'supervisor', 'executive', 'director', 'manager'],
        'licensing_scope': ['license', 'scope', 'certification', 'credential', 'accreditation', 'board certified'],
        'childcare': ['childcare', 'child care', 'daycare', 'family'],
        'culture_dei': ['culture', 'diversity', 'inclusion', 'equity', 'dei', 'cultural competence'],
        'housing_transportation': ['housing', 'transportation', 'affordable housing', 'commute', 'travel'],
        'primary_care': ['primary care', 'family medicine', 'general practice'],
        'staffing_shortage': ['shortage', 'understaffed', 'vacant', 'recruitment', 'retention', 'turnover'],
        'technology_training': ['technology', 'digital', 'system', 'electronic', 'ai', 'telehealth', 'emr'],
        'professional_development': ['development', 'training', 'education', 'skills', 'cme', 'continuing education'],
        'simulation_training': ['simulation', 'sim', 'hands-on', 'skills lab'],
        'recruitment_challenges': ['recruit', 'hire', 'attract', 'pipeline'],
        'clinical_competency': ['clinical', 'competency', 'skills', 'patient care', 'evidence-based'],
        'interdisciplinary_care': ['interdisciplinary', 'team-based', 'collaborative', 'multidisciplinary'],
        'specialty_care': ['specialist', 'specialty', 'subspecialty', 'quaternary'],
        'rural_care': ['rural', 'underserved', 'community clinic', 'critical access'],
        'nursing_specific': ['nursing', 'nurse', 'rn', 'lpn', 'cna', 'bsn'],
        'physician_specific': ['physician', 'doctor', 'md', 'resident', 'fellowship'],
        'allied_health': ['respiratory', 'radiology', 'laboratory', 'pharmacy', 'physical therapy', 'occupational therapy'],
        'academic_training': ['residency', 'fellowship', 'medical school', 'university', 'academic'],
        'quality_safety': ['quality', 'safety', 'outcomes', 'patient safety', 'quality improvement']
    }
    
    found_phrases = []
    for phrase_key, keywords in key_phrases.items():
        if any(keyword in text_str for keyword in keywords):
            found_phrases.append(phrase_key)
    
    return found_phrases

def create_tag_dimension():
    """Create the tag dimension table"""
    
    tags = [
        {'TagID': 1, 'TagKey': 'compensation_incentives', 'TagName': 'Compensation & Incentives', 'TagCategory': 'Financial', 'TagPriority': 'High'},
        {'TagID': 2, 'TagKey': 'behavioral_health_need', 'TagName': 'Behavioral Health Need', 'TagCategory': 'Clinical', 'TagPriority': 'High'},
        {'TagID': 3, 'TagKey': 'burnout_wellbeing', 'TagName': 'Burnout & Wellbeing', 'TagCategory': 'Wellness', 'TagPriority': 'High'},
        {'TagID': 4, 'TagKey': 'funding_grants', 'TagName': 'Funding & Grants', 'TagCategory': 'Financial', 'TagPriority': 'Medium'},
        {'TagID': 5, 'TagKey': 'leadership_development', 'TagName': 'Leadership Development', 'TagCategory': 'Professional', 'TagPriority': 'High'},
        {'TagID': 6, 'TagKey': 'licensing_scope', 'TagName': 'Licensing & Scope', 'TagCategory': 'Regulatory', 'TagPriority': 'Medium'},
        {'TagID': 7, 'TagKey': 'childcare', 'TagName': 'Childcare Support', 'TagCategory': 'Support', 'TagPriority': 'Medium'},
        {'TagID': 8, 'TagKey': 'culture_dei', 'TagName': 'Culture & DEI', 'TagCategory': 'Organizational', 'TagPriority': 'Medium'},
        {'TagID': 9, 'TagKey': 'housing_transportation', 'TagName': 'Housing & Transportation', 'TagCategory': 'Support', 'TagPriority': 'High'},
        {'TagID': 10, 'TagKey': 'primary_care', 'TagName': 'Primary Care', 'TagCategory': 'Clinical', 'TagPriority': 'Medium'},
        {'TagID': 11, 'TagKey': 'staffing_shortage', 'TagName': 'Staffing Shortage', 'TagCategory': 'Workforce', 'TagPriority': 'High'},
        {'TagID': 12, 'TagKey': 'technology_training', 'TagName': 'Technology Training', 'TagCategory': 'Technology', 'TagPriority': 'Medium'},
        {'TagID': 13, 'TagKey': 'professional_development', 'TagName': 'Professional Development', 'TagCategory': 'Professional', 'TagPriority': 'High'},
        {'TagID': 14, 'TagKey': 'simulation_training', 'TagName': 'Simulation Training', 'TagCategory': 'Training', 'TagPriority': 'Medium'},
        {'TagID': 15, 'TagKey': 'recruitment_challenges', 'TagName': 'Recruitment Challenges', 'TagCategory': 'Workforce', 'TagPriority': 'High'},
        {'TagID': 16, 'TagKey': 'clinical_competency', 'TagName': 'Clinical Competency', 'TagCategory': 'Clinical', 'TagPriority': 'High'},
        {'TagID': 17, 'TagKey': 'interdisciplinary_care', 'TagName': 'Interdisciplinary Care', 'TagCategory': 'Collaboration', 'TagPriority': 'Medium'},
        {'TagID': 18, 'TagKey': 'specialty_care', 'TagName': 'Specialty Care', 'TagCategory': 'Clinical', 'TagPriority': 'High'},
        {'TagID': 19, 'TagKey': 'rural_care', 'TagName': 'Rural Care', 'TagCategory': 'Geographic', 'TagPriority': 'Medium'},
        {'TagID': 20, 'TagKey': 'nursing_specific', 'TagName': 'Nursing Specific', 'TagCategory': 'Profession', 'TagPriority': 'High'},
        {'TagID': 21, 'TagKey': 'physician_specific', 'TagName': 'Physician Specific', 'TagCategory': 'Profession', 'TagPriority': 'High'},
        {'TagID': 22, 'TagKey': 'allied_health', 'TagName': 'Allied Health', 'TagCategory': 'Profession', 'TagPriority': 'Medium'},
        {'TagID': 23, 'TagKey': 'academic_training', 'TagName': 'Academic Training', 'TagCategory': 'Education', 'TagPriority': 'Medium'},
        {'TagID': 24, 'TagKey': 'quality_safety', 'TagName': 'Quality & Safety', 'TagCategory': 'Clinical', 'TagPriority': 'High'}
    ]
    
    for tag in tags:
        tag['TagDescription'] = f"Analysis tag for {tag['TagName'].lower()}"
        tag['IsActive'] = 1
    
    df = pd.DataFrame(tags)
    print(f"🏷️ Created DimTags with {len(df)} tag definitions")
    
    return df

def create_individual_response_tag_bridge(fact_table, dim_tags):
    """Create bridge table linking individual response records to specific tags"""
    
    bridge_tags = []
    
    # Analyze each individual response in the fact table
    for _, fact_row in fact_table.iterrows():
        response_id = fact_row['ResponseID']
        response_text = str(fact_row['ResponseText']) if pd.notna(fact_row['ResponseText']) else ''
        
        # Only analyze responses that have actual text content
        if response_text.strip() and fact_row['HasResponse'] == 1:
            # Extract key phrases from this specific response
            found_phrases = extract_key_phrases(response_text)
            
            for phrase in found_phrases:
                # Find tag ID
                tag_matches = dim_tags[dim_tags['TagKey'] == phrase]
                if len(tag_matches) > 0:
                    tag_id = tag_matches.iloc[0]['TagID']
                    tag_name = tag_matches.iloc[0]['TagName']
                    tag_category = tag_matches.iloc[0]['TagCategory']
                    
                    bridge_tags.append({
                        'ResponseID': response_id,
                        'TagID': tag_id,
                        'TagKey': phrase,
                        'TagName': tag_name,
                        'TagCategory': tag_category,
                        'ResponseText': response_text[:100] + '...' if len(response_text) > 100 else response_text  # Preview of response
                    })
    
    df_bridge = pd.DataFrame(bridge_tags)
    print(f"🔗 Created BridgeResponseTags with {len(df_bridge)} individual response tag links")
    if len(df_bridge) > 0:
        print(f"   📊 Covering {df_bridge['ResponseID'].nunique()} individual responses")
        print(f"   🏷️ Most common tags: {df_bridge['TagName'].value_counts().head(3).to_dict()}")
    
    return df_bridge

if __name__ == "__main__":
    # Test the dimension creation
    from data_loader import load_survey_data
    from fact_survey_responses import create_fact_table
    from dim_geography import create_geography_dimension
    from dim_organization import create_organization_dimension
    from dim_role import create_role_dimension
    from dim_urgency import create_urgency_dimension
    from dim_question import create_question_dimension
    
    print("Testing individual response tag analysis...")
    df = load_survey_data()
    if df is not None:
        # Create required dimensions
        dim_geography = create_geography_dimension(df)
        dim_organization = create_organization_dimension(df)
        dim_role = create_role_dimension(df)
        dim_urgency = create_urgency_dimension()
        dim_question = create_question_dimension(df)
        
        # Create fact table
        fact_table = create_fact_table(df, dim_geography, dim_organization, dim_urgency, dim_question, dim_role)
        
        # Create tags
        dim_tags = create_tag_dimension()
        bridge_df = create_individual_response_tag_bridge(fact_table, dim_tags)
        
        # Show sample results
        if len(bridge_df) > 0:
            print("\nSample tagged responses:")
            print(bridge_df[['ResponseID', 'TagName', 'ResponseText']].head())
