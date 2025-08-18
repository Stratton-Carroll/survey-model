"""
Healthcare taxonomy definitions for categorization and analysis
"""

# Healthcare domain categories with enhanced metadata
HEALTHCARE_CATEGORIES = {
    'training_development': {
        'keywords': ['training', 'education', 'development', 'skills', 'learning', 'certification', 
                    'competency', 'professional development', 'continuing education', 'simulation',
                    'workshop', 'course', 'curriculum', 'mentoring', 'coaching'],
        'description': 'Training, education, and skill development needs',
        'priority_weight': 1.0,
        'domain': 'Education'
    },
    'recruitment': {
        'keywords': ['recruit', 'hiring', 'attract', 'new graduates', 'pipeline', 'talent acquisition',
                    'onboarding', 'job posting', 'interview', 'selection'],
        'description': 'Strategies and challenges in recruiting healthcare professionals',
        'priority_weight': 0.9,
        'domain': 'Workforce'
    },
    'retention': {
        'keywords': ['retain', 'turnover', 'stay', 'keep', 'attrition', 'engagement', 'satisfaction',
                    'loyalty', 'commitment', 'longevity', 'resign', 'quit', 'leaving'],
        'description': 'Retention strategies and factors affecting staff staying',
        'priority_weight': 0.9,
        'domain': 'Workforce'
    },
    'leadership_management': {
        'keywords': ['leadership', 'management', 'supervision', 'mentoring', 'coaching', 'supervisor', 
                    'manager', 'executive', 'director', 'administrative', 'governance'],
        'description': 'Leadership development and management training needs',
        'priority_weight': 0.8,
        'domain': 'Leadership'
    },
    'clinical_competencies': {
        'keywords': ['clinical', 'patient care', 'bedside', 'nursing', 'medical', 'diagnostic', 
                    'therapeutic', 'clinical skills', 'evidence-based', 'practice', 'protocols'],
        'description': 'Clinical skills and patient care competencies',
        'priority_weight': 1.0,
        'domain': 'Clinical'
    },
    'technology_innovation': {
        'keywords': ['technology', 'electronic', 'digital', 'system', 'innovation', 'equipment', 
                    'simulation', 'virtual', 'emr', 'ehr', 'software', 'automation'],
        'description': 'Technology adoption and digital health initiatives',
        'priority_weight': 0.7,
        'domain': 'Technology'
    },
    'interprofessional_collaboration': {
        'keywords': ['interdisciplinary', 'collaboration', 'teamwork', 'communication', 'interprofessional',
                    'team-based', 'coordination', 'partnership', 'cooperation'],
        'description': 'Team-based care and interprofessional collaboration',
        'priority_weight': 0.8,
        'domain': 'Collaboration'
    },
    'resource_constraints': {
        'keywords': ['cost', 'budget', 'funding', 'resources', 'financial', 'money', 'expensive', 'afford',
                    'economic', 'investment', 'roi', 'price'],
        'description': 'Financial and resource limitations',
        'priority_weight': 0.6,
        'domain': 'Resources'
    },
    'time_constraints': {
        'keywords': ['time', 'schedule', 'busy', 'coverage', 'staffing', 'hours', 'availability',
                    'workload', 'overtime', 'shift', 'scheduling'],
        'description': 'Time and scheduling challenges',
        'priority_weight': 0.6,
        'domain': 'Operations'
    },
    'career_advancement': {
        'keywords': ['career', 'advancement', 'promotion', 'progression', 'mobility', 'growth',
                    'opportunity', 'pathway', 'ladder', 'development'],
        'description': 'Career development and advancement opportunities',
        'priority_weight': 0.7,
        'domain': 'Workforce'
    },
    'work_life_balance': {
        'keywords': ['work-life', 'balance', 'wellbeing', 'burnout', 'stress', 'flexibility', 'family',
                    'wellness', 'mental health', 'resilience', 'self-care'],
        'description': 'Work-life balance and wellness initiatives',
        'priority_weight': 0.8,
        'domain': 'Wellness'
    },
    'quality_improvement': {
        'keywords': ['quality', 'improvement', 'outcomes', 'safety', 'best practices', 'standards',
                    'accreditation', 'metrics', 'performance', 'excellence'],
        'description': 'Quality improvement and patient safety initiatives',
        'priority_weight': 0.9,
        'domain': 'Quality'
    }
}

# Healthcare roles with categorization
HEALTHCARE_ROLES = {
    'nursing': {
        'keywords': ['nurse', 'rn', 'lpn', 'cna', 'nursing', 'registered nurse', 'licensed practical nurse'],
        'category': 'Direct Care',
        'seniority': 'Staff'
    },
    'physicians': {
        'keywords': ['physician', 'doctor', 'md', 'do', 'hospitalist', 'attending', 'resident', 'fellow'],
        'category': 'Direct Care', 
        'seniority': 'Provider'
    },
    'allied_health': {
        'keywords': ['therapist', 'technician', 'tech', 'respiratory', 'radiology', 'lab', 'pharmacy',
                     'physical therapy', 'occupational therapy', 'speech therapy', 'social work'],
        'category': 'Support Care',
        'seniority': 'Staff'
    },
    'leadership': {
        'keywords': ['ceo', 'coo', 'director', 'manager', 'supervisor', 'administrator', 'chief',
                    'vice president', 'president', 'executive'],
        'category': 'Management',
        'seniority': 'Leadership'
    },
    'support_staff': {
        'keywords': ['clerk', 'registration', 'housekeeping', 'transport', 'security', 'maintenance',
                     'food service', 'environmental services'],
        'category': 'Operations',
        'seniority': 'Staff'
    }
}

# Urgency level definitions
URGENCY_INDICATORS = {
    'high': {
        'keywords': ['urgent', 'critical', 'immediate', 'crisis', 'shortage', 'emergency', 'severe',
                    'desperate', 'dire', 'pressing', 'acute'],
        'score': 3,
        'description': 'Critical and immediate needs requiring urgent attention'
    },
    'medium': {
        'keywords': ['important', 'needed', 'priority', 'significant', 'essential', 'necessary',
                    'required', 'vital', 'key'],
        'score': 2,
        'description': 'Important priorities that should be addressed systematically'
    },
    'low': {
        'keywords': ['would like', 'prefer', 'nice to have', 'future', 'eventually', 'someday',
                    'optional', 'ideal', 'wish'],
        'score': 1,
        'description': 'Future considerations and nice-to-have improvements'
    }
}

# Geographic regions for Arkansas
NWA_REGIONS = {
    'Washington': 'Northwest Arkansas',
    'Benton': 'Northwest Arkansas', 
    'Madison': 'Northwest Arkansas',
    'Carroll': 'Northwest Arkansas',
    'Newton': 'North Central Arkansas',
    'Boone': 'North Central Arkansas',
    'Searcy': 'North Central Arkansas',
    'Marion': 'North Central Arkansas',
    'Baxter': 'North Central Arkansas',
    'Stone': 'North Central Arkansas',
    'Van Buren': 'North Central Arkansas',
    'Conway': 'Central Arkansas',
    'Cleburne': 'Central Arkansas',
    'Faulkner': 'Central Arkansas',
    'Saline': 'Central Arkansas'
}

print("🏥 Healthcare taxonomy loaded successfully!")
