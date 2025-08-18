"""
CONSOLIDATED Individual Response Tag Analysis
Streamlined to 15 high-impact tags with smart consolidations
"""

import pandas as pd
import sys
import os
from collections import Counter
import re

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

from healthcare_taxonomy import HEALTHCARE_CATEGORIES

def extract_key_phrases(text, max_tags=4):
    """
    Extract meaningful key phrases from text with improved accuracy
    - Uses contextual keyword matching
    - Implements relevance scoring
    - Limits number of tags per response
    """
    if pd.isna(text) or not text or str(text).strip() == '':
        return []
    
    text_str = str(text).lower()
    
    # Define consolidated key phrases with merged categories
    key_phrases = {
        'compensation_incentives': {
            'primary_keywords': ['compensation', 'salary', 'pay', 'wage', 'bonus', 'incentive', 'sign on bonus'],
            'secondary_keywords': ['financial incentive', 'tuition assistance', 'student loan', 'pay well', 'no money', 'paying student loans', 'loan forgiveness'],
            'context_keywords': ['increase', 'competitive', 'better', 'higher', 'financial', 'money'],
            'negative_keywords': [],
            'min_score': 1
        },
        'behavioral_health_need': {
            'primary_keywords': ['behavioral health', 'mental health', 'psychology', 'psychiatry', 'psychiatric care', 'psychiatric'],
            'secondary_keywords': ['counseling', 'therapy', 'trauma', 'addiction', 'psych eval', 'mental health services'],
            'context_keywords': ['services', 'treatment', 'support', 'care', 'patients'],
            'negative_keywords': [],
            'min_score': 2
        },
        'burnout_wellbeing': {
            'primary_keywords': ['burnout', 'burn out', 'wellbeing', 'wellness', 'work-life balance', 'work life balance'],
            'secondary_keywords': ['stress', 'exhaustion', 'fatigue', 'self-care', 'worn down', 'wears down', 'overworked', 'dissatisfaction'],
            'context_keywords': ['management', 'prevention', 'support', 'balance', 'employees'],
            'negative_keywords': [],
            'min_score': 1
        },
        'funding_grants': {
            'primary_keywords': ['funding', 'grant', 'budget'],
            'secondary_keywords': ['financial support', 'resources to pay', 'tuition reimbursement', 'tuition assistance'],
            'context_keywords': ['federal', 'state', 'apply', 'seek'],
            'negative_keywords': [],
            'min_score': 2
        },
        'leadership_development': {
            'primary_keywords': ['leadership development', 'leadership training', 'management training', 'supervision', 'leadership tracks'],
            'secondary_keywords': ['leadership', 'management', 'supervisor training', 'executive', 'supervision skills', 'leaders'],
            'context_keywords': ['skills', 'program', 'course', 'promotion', 'training at each level'],
            'negative_keywords': ['clinical leadership', 'thought leadership'],
            'min_score': 1
        },
        'licensing_scope': {
            'primary_keywords': ['license', 'licensing', 'scope of practice', 'certification'],
            'secondary_keywords': ['credential', 'accreditation', 'board certified'],
            'context_keywords': ['requirements', 'maintain', 'renew'],
            'negative_keywords': [],
            'min_score': 2
        },
        'childcare': {
            'primary_keywords': ['childcare', 'child care', 'daycare'],
            'secondary_keywords': ['family support', 'dependent care'],
            'context_keywords': ['benefits', 'assistance', 'services'],
            'negative_keywords': ['pediatric care', 'child health'],
            'min_score': 2
        },
        'housing_transportation': {
            'primary_keywords': ['housing', 'transportation', 'affordable housing'],
            'secondary_keywords': ['commute', 'travel', 'relocation', 'finding housing'],
            'context_keywords': ['assistance', 'support', 'stipend', 'crisis', 'help with'],
            'negative_keywords': ['patient transport', 'medical transport'],
            'min_score': 1
        },
        'workforce_challenges': {
            'primary_keywords': [
                # Shortage keywords
                'shortage', 'understaffed', 'short staffed', 'staffing shortage', 
                'gaping hole', 'lack of', 'not enough', 'scarce', 'vacant',
                'hard to hire', 'difficult to hire', 'can\'t hire', 'unable to hire', 'my own billing', 'we need', 'we also need', 'need a', 'need more', 'gaps', 'are needed',
                # Recruitment keywords
                'recruitment', 'recruiting', 'hire', 'hiring', 'attract'
            ],
            'secondary_keywords': [
                # Shortage keywords
                'turnover', 'high turnover', 'leaving', 'staff leaving', 'people leaving',
                'contract staff', 'temp workers', 'agency staff', 'retention',
                'empty positions', 'open positions', 'need more', 'need staff',
                'more people', 'more workers', 'fill positions', 'desperately need',
                'critical need', 'bottleneck', 'could double enrollment', 'my own billing', 'we need', 'we also need', 'need a', 'need more', 'gaps', 'are needed',
                # Recruitment keywords
                'pipeline', 'talent acquisition', 'market', 'marketing', 'compete', 'competitive'
            ],
            'context_keywords': [
                'workforce', 'positions', 'roles', 'employees', 'staff', 'workers',
                'hiring', 'recruitment', 'talent', 'personnel', 'challenges', 'difficulty', 
                'hard to', 'better', 'exceptional place'
            ],
            'negative_keywords': [],
            'min_score': 2
        },
        'training_development': {
            'primary_keywords': [
                # Professional Development
                'professional development', 'continuing education', 'cme', 'continuing ed',
                # Academic Training
                'residency', 'fellowship', 'medical school',  'terminology',
                # Simulation Training
                'simulation', 'sim lab', 'simulation training',
                # Technology Training
                'technology training', 'tech training', 'digital training', 'emr', 'technology integration'
            ],
            'secondary_keywords': [
                # Professional Development
                'career development', 'skill development', 'conferences', 'educators',
                # Academic Training
                'university', 'academic', 'rotation', 'terminology',
                # Simulation Training
                'hands-on training', 'skills lab', 'practice lab',
                # Technology Training
                'emr training', 'software training', 'system training', 'clinical decision tools', 'systems innovation', 'emr advancements'
            ],
            'context_keywords': [
                'opportunities', 'program', 'support', 'grow', 'introduced', 'training', 
                'education', 'practice', 'lab', 'computer', 'digital', 'electronic', 'innovation', 'tools'
            ],
            'negative_keywords': ['leadership development', 'leadership training'],
            'min_score': 2
        },
        'clinical_services': {
            'primary_keywords': [
                # Specialty Care
                'specialist', 'specialty care', 'subspecialty',
                # Primary Care
                'primary care', 'family medicine', 'family physician', 'primary care physician',
                # Interdisciplinary Care
                'interdisciplinary', 'multidisciplinary', 'team-based care'
            ],
            'secondary_keywords': [
                # Specialty Care
                'specialized', 'quaternary care',
                # Primary Care
                'general practice', 'family doctor', 'pcp',
                # Interdisciplinary Care
                'collaborative care', 'care coordination'
            ],
            'context_keywords': [
                'referral', 'specialized', 'advanced', 'preventive', 'routine', 'general',
                'team', 'collaboration', 'coordination'
            ],
            'negative_keywords': [],
            'min_score': 2
        },
        'clinical_competency': {
            'primary_keywords': ['clinical competency', 'clinical skills', 'patient care skills'],
            'secondary_keywords': ['bedside manner', 'clinical training'],
            'context_keywords': ['evidence-based', 'best practices', 'quality'],
            'negative_keywords': [],
            'min_score': 2
        },
        'quality_safety': {
            'primary_keywords': ['quality improvement', 'patient safety', 'quality assurance'],
            'secondary_keywords': ['outcomes', 'safety', 'quality'],
            'context_keywords': ['improvement', 'measures', 'initiatives'],
            'negative_keywords': [],
            'min_score': 2
        },
        'rural_care': {
            'primary_keywords': ['rural health', 'rural care', 'rural hospital', 'rural community'],
            'secondary_keywords': ['rural areas', 'rural', 'geographic locations in rural'],
            'context_keywords': ['remote', 'isolated', 'distance'],
            'negative_keywords': [],
            'min_score': 2
        },
        'allied_health': {
            'primary_keywords': ['social worker', 'social workers', 'patient navigator', 'patient navigators'],
            'secondary_keywords': ['laboratory technician', 'lab tech', 'respiratory therapist', 'rad tech', 'dietitian', 'physical therapist', 'occupational therapist', 'allied health'],
            'context_keywords': ['technician', 'therapist', 'navigator', 'support staff'],
            'negative_keywords': ['nursing', 'physician', 'doctor'],
            'min_score': 1
        }
    }
    
    # Calculate relevance scores for each phrase
    phrase_scores = {}
    
    for phrase_key, phrase_config in key_phrases.items():
        score = 0
        
        # Primary keywords (highest weight)
        for keyword in phrase_config['primary_keywords']:
            if keyword in text_str:
                score += 3
        
        # Secondary keywords (medium weight)
        for keyword in phrase_config['secondary_keywords']:
            if keyword in text_str:
                score += 2
        
        # Context keywords (lower weight, but helps with relevance)
        for keyword in phrase_config['context_keywords']:
            if keyword in text_str:
                score += 1
        
        # Apply negative keywords (reduces score)
        for neg_keyword in phrase_config['negative_keywords']:
            if neg_keyword in text_str:
                score -= 2
        
        # Only include if meets minimum score threshold
        if score >= phrase_config['min_score']:
            phrase_scores[phrase_key] = score
    
    # Sort by score and limit to max_tags
    sorted_phrases = sorted(phrase_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return top scoring phrases up to max_tags limit
    return [phrase for phrase, score in sorted_phrases[:max_tags]]

def create_tag_dimension():
    """Create the consolidated tag dimension table with 15 streamlined tags"""
    
    tags = [
        # High Impact Tags (Top 4)
        {'TagID': 1, 'TagKey': 'behavioral_health_need', 'TagName': 'Behavioral Health Need', 'TagCategory': 'Clinical', 'TagPriority': 'High'},
        {'TagID': 2, 'TagKey': 'leadership_development', 'TagName': 'Leadership Development', 'TagCategory': 'Professional', 'TagPriority': 'High'},
        {'TagID': 3, 'TagKey': 'compensation_incentives', 'TagName': 'Compensation & Incentives', 'TagCategory': 'Financial', 'TagPriority': 'High'},
        {'TagID': 4, 'TagKey': 'burnout_wellbeing', 'TagName': 'Burnout & Wellbeing', 'TagCategory': 'Wellness', 'TagPriority': 'High'},
        
        # Medium Impact Tags (Consolidated)
        {'TagID': 5, 'TagKey': 'workforce_challenges', 'TagName': 'Workforce Challenges', 'TagCategory': 'Workforce', 'TagPriority': 'High'},
        {'TagID': 6, 'TagKey': 'training_development', 'TagName': 'Training & Development', 'TagCategory': 'Professional', 'TagPriority': 'High'},
        {'TagID': 7, 'TagKey': 'housing_transportation', 'TagName': 'Housing & Transportation', 'TagCategory': 'Support', 'TagPriority': 'Medium'},
        {'TagID': 8, 'TagKey': 'funding_grants', 'TagName': 'Funding & Grants', 'TagCategory': 'Financial', 'TagPriority': 'Medium'},
        
        # Lower Impact Tags (Specific but Important)
        {'TagID': 9, 'TagKey': 'clinical_services', 'TagName': 'Clinical Services', 'TagCategory': 'Clinical', 'TagPriority': 'Medium'},
        {'TagID': 10, 'TagKey': 'licensing_scope', 'TagName': 'Licensing & Scope', 'TagCategory': 'Regulatory', 'TagPriority': 'Medium'},
        {'TagID': 11, 'TagKey': 'quality_safety', 'TagName': 'Quality & Safety', 'TagCategory': 'Clinical', 'TagPriority': 'Medium'},
        {'TagID': 12, 'TagKey': 'childcare', 'TagName': 'Childcare Support', 'TagCategory': 'Support', 'TagPriority': 'Medium'},
        {'TagID': 13, 'TagKey': 'rural_care', 'TagName': 'Rural Care', 'TagCategory': 'Geographic', 'TagPriority': 'Medium'},
        {'TagID': 14, 'TagKey': 'clinical_competency', 'TagName': 'Clinical Competency', 'TagCategory': 'Clinical', 'TagPriority': 'Medium'},
        {'TagID': 15, 'TagKey': 'allied_health', 'TagName': 'Allied Health', 'TagCategory': 'Profession', 'TagPriority': 'Medium'}
    ]
    
    for tag in tags:
        tag['TagDescription'] = f"Analysis tag for {tag['TagName'].lower()}"
        tag['IsActive'] = 1
    
    df = pd.DataFrame(tags)
    print(f"🏷️ Created CONSOLIDATED DimTags with {len(df)} streamlined tag definitions")
    print(f"   📊 Consolidated from 22 tags to 15 high-impact tags")
    print(f"   🎯 Merged: Training categories, Workforce categories, Clinical services")
    
    return df

def create_individual_response_tag_bridge(fact_table, dim_tags):
    """Create improved bridge table with consolidated tag accuracy"""
    
    bridge_tags = []
    tag_stats = {
        'total_responses_processed': 0,
        'responses_with_tags': 0,
        'total_tags_assigned': 0,
        'responses_with_max_tags': 0
    }
    
    # Analyze each individual response in the fact table
    for _, fact_row in fact_table.iterrows():
        response_id = fact_row['ResponseID']
        response_text = str(fact_row['ResponseText']) if pd.notna(fact_row['ResponseText']) else ''
        
        tag_stats['total_responses_processed'] += 1
        
        # Only analyze responses that have actual text content
        if response_text.strip() and fact_row['HasResponse'] == 1:
            # Extract key phrases with improved algorithm (max 4 tags)
            found_phrases = extract_key_phrases(response_text, max_tags=4)
            
            if found_phrases:
                tag_stats['responses_with_tags'] += 1
                tag_stats['total_tags_assigned'] += len(found_phrases)
                
                if len(found_phrases) == 4:
                    tag_stats['responses_with_max_tags'] += 1
            
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
                        'ResponseText': response_text[:100] + '...' if len(response_text) > 100 else response_text
                    })
    
    df_bridge = pd.DataFrame(bridge_tags)
    
    # Print consolidated statistics
    print(f"🔗 CONSOLIDATED BridgeResponseTags created:")
    print(f"   📊 {len(df_bridge)} tag links")
    print(f"   📝 {tag_stats['responses_with_tags']} responses tagged")
    print(f"   🏷️ Avg tags per response: {tag_stats['total_tags_assigned'] / max(tag_stats['responses_with_tags'], 1):.2f}")
    print(f"   🎯 {tag_stats['responses_with_max_tags']} responses with max tags (4)")
    print(f"   🎨 Streamlined for better analytics and reporting")
    
    if len(df_bridge) > 0:
        print(f"   📈 Most common tags: {df_bridge['TagName'].value_counts().head(3).to_dict()}")
    
    return df_bridge

if __name__ == "__main__":
    # Test the consolidated dimension creation
    from data_loader import load_survey_data
    from fact_survey_responses import create_fact_table
    from dim_geography import create_geography_dimension
    from dim_organization import create_organization_dimension
    from dim_role import create_role_dimension
    from dim_urgency import create_urgency_dimension
    from dim_question import create_question_dimension
    
    print("Testing CONSOLIDATED individual response tag analysis...")
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
        
        # Create consolidated tags
        dim_tags = create_tag_dimension()
        bridge_df = create_individual_response_tag_bridge(fact_table, dim_tags)
        
        # Show sample results
        if len(bridge_df) > 0:
            print("\nSample tagged responses with consolidated tags:")
            print(bridge_df[['ResponseID', 'TagName', 'ResponseText']].head())
            
            print(f"\nConsolidated tag distribution:")
            print(bridge_df['TagName'].value_counts())