"""
Question Dimension Table Creation
"""

import pandas as pd
import sys
import os

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

def create_question_dimension(df):
    """Create the question dimension table"""
    
    # Structured columns that are not survey questions
    excluded_columns = [
        'Start time', 'Completion time', 'Organization', 'Organization County', 
        'Primary_County', 'Service_Area', 'Multi_County_Flag', 'Role/Position', 
        'Length of time in current position', 'Role_Standardized', 'Role_Category', 
        'Role_Level', 'Role_Type', 'Time_Range_Category', 'Contact Email'
    ]
    
    dim_question = []
    question_id = 1
    
    for col in df.columns:
        if col not in excluded_columns:
            # Calculate response statistics
            response_count = df[col].notna().sum()
            response_rate = (response_count / len(df)) * 100
            
            # Determine question type based on content
            if 'consent' in col.lower():
                question_type = 'Consent'
            elif any(phrase in col.lower() for phrase in ['select your top', 'choices', '(select']):
                question_type = 'Multiple Choice'
            elif any(word in col.lower() for word in ['travel', 'often', 'far']):
                question_type = 'Scale/Frequency'
            elif len(col) > 80:  # Long question text indicates open-ended
                question_type = 'Open-Ended'
            else:
                question_type = 'Short Answer'
            
            # Create short identifier for long questions
            if len(col) > 100:
                # Try to extract key words for short version
                if 'skills' in col.lower() and 'priority' in col.lower():
                    question_short = 'Priority Skills & Resources'
                elif 'challenge' in col.lower() and 'preventing' in col.lower():
                    question_short = 'Challenges Preventing Action'
                elif 'training needs' in col.lower() and 'currently' in col.lower():
                    question_short = 'Current Training Methods'
                elif 'retain' in col.lower() and 'health care professionals' in col.lower():
                    question_short = 'Retention Strategies'
                elif 'recruit' in col.lower() and 'health care professionals' in col.lower():
                    question_short = 'Recruitment Strategies'
                elif 'leadership levels' in col.lower():
                    question_short = 'Leadership Training Needs'
                elif 'elevate and advance' in col.lower():
                    question_short = 'Professional Advancement Actions'
                elif 'most significant training' in col.lower() and 'needs' in col.lower():
                    question_short = 'Groups with Training Needs'
                elif 'highest training' in col.lower() and 'needs' in col.lower():
                    question_short = 'Groups with Highest Needs'
                elif 'travel' in col.lower() and 'center for excellence' in col.lower():
                    question_short = 'Travel Distance Willingness'
                elif 'interdisciplinary' in col.lower() and 'engage' in col.lower():
                    question_short = 'Current Interdisciplinary Training'
                elif 'interdisciplinary' in col.lower() and 'require' in col.lower():
                    question_short = 'Desired Interdisciplinary Training'
                elif 'center for health care workforce excellence' in col.lower():
                    question_short = 'Important Center Features'
                elif 'simulation center' in col.lower() and 'facilities' in col.lower():
                    question_short = 'Desired Simulation Facilities'
                elif 'final comments' in col.lower():
                    question_short = 'Final Comments & Suggestions'
                else:
                    question_short = col[:50] + '...'
            else:
                question_short = col
            
            dim_question.append({
                'QuestionID': question_id,
                'QuestionText': col,
                'QuestionShort': question_short,
                'QuestionType': question_type,
                'ResponseCount': response_count,
                'ResponseRate': round(response_rate, 1),
                'IsRequired': 1 if response_rate > 90 else 0,
                'IsOpenEnded': 1 if question_type == 'Open-Ended' else 0
            })
            question_id += 1
    
    df_result = pd.DataFrame(dim_question)
    print(f"❓ Created DimQuestion with {len(df_result)} questions")
    
    return df_result

if __name__ == "__main__":
    # Test the dimension creation
    from data_loader import load_survey_data
    df = load_survey_data()
    if df is not None:
        dim_df = create_question_dimension(df)
        print(dim_df.head())
