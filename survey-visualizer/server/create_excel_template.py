#!/usr/bin/env python3
"""
Create Excel template for question-tag mappings
"""

import pandas as pd
import os

def create_excel_template():
    """Create Excel template with sample data and instructions"""
    
    # Sample data showing the structure
    sample_data = [
        {
            'QuestionID': 1,
            'TagName': 'Compensation & Incentives', 
            'TagType': 'Primary',
            'AssignmentType': 'AUTOMATIC',
            'Notes': 'Always assign for compensation-related questions',
            'AppliedBy': 'Survey Team'
        },
        {
            'QuestionID': 1,
            'TagName': 'Sign-on Bonuses',
            'TagType': 'Sub', 
            'AssignmentType': 'CONDITIONAL',
            'Notes': 'Only if response mentions signing bonuses',
            'AppliedBy': 'Survey Team'
        },
        {
            'QuestionID': 2,
            'TagName': 'Workforce Challenges',
            'TagType': 'Primary',
            'AssignmentType': 'AUTOMATIC', 
            'Notes': 'Standard for workforce questions',
            'AppliedBy': 'Survey Team'
        },
        {
            'QuestionID': 2,
            'TagName': 'Recruitment Challenges',
            'TagType': 'Sub',
            'AssignmentType': 'SUGGESTED',
            'Notes': 'Suggest this sub-tag for review',
            'AppliedBy': 'Survey Team'
        }
    ]
    
    # Instructions data
    instructions_data = [
        {'Field': 'QuestionID', 'Description': 'Integer question ID (1, 2, 3, etc.)', 'Required': 'Yes', 'Valid Values': 'Any integer'},
        {'Field': 'TagName', 'Description': 'Exact tag name from database', 'Required': 'Yes', 'Valid Values': 'Must match existing tag names'},
        {'Field': 'TagType', 'Description': 'Whether this is a primary or sub-tag', 'Required': 'Yes', 'Valid Values': 'Primary, Sub'},
        {'Field': 'AssignmentType', 'Description': 'How this tag should be applied', 'Required': 'Yes', 'Valid Values': 'AUTOMATIC, CONDITIONAL, SUGGESTED'},
        {'Field': 'Notes', 'Description': 'Optional explanation or conditions', 'Required': 'No', 'Valid Values': 'Free text'},
        {'Field': 'AppliedBy', 'Description': 'Who made this mapping', 'Required': 'No', 'Valid Values': 'Free text'}
    ]
    
    assignment_type_help = [
        {'AssignmentType': 'AUTOMATIC', 'Description': 'Always assign this tag to responses for this question'},
        {'AssignmentType': 'CONDITIONAL', 'Description': 'Assign only if keywords match (combines with existing algorithm)'},
        {'AssignmentType': 'SUGGESTED', 'Description': 'Show as suggested tag in UI for manual review'}
    ]
    
    # Create directory if it doesn't exist
    template_dir = "/Users/strattoncarroll/Documents/survey-model/excel_templates"
    os.makedirs(template_dir, exist_ok=True)
    
    # Write to Excel file
    template_path = os.path.join(template_dir, "QuestionTagMapping_Template.xlsx")
    
    with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
        # Main data sheet
        pd.DataFrame(sample_data).to_excel(writer, sheet_name='QuestionTagMappings', index=False)
        
        # Instructions sheet
        pd.DataFrame(instructions_data).to_excel(writer, sheet_name='Instructions', index=False)
        
        # Assignment type help
        pd.DataFrame(assignment_type_help).to_excel(writer, sheet_name='AssignmentTypes', index=False)
        
    print(f"Excel template created at: {template_path}")
    return template_path

if __name__ == "__main__":
    create_excel_template()