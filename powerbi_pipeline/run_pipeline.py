"""
Main pipeline orchestrator
Runs all dimension and fact table creation in proper order
"""

import sys
import os
import time

# Add pipeline directory to path for imports
sys.path.append(os.path.dirname(__file__))

def run_pipeline():
    """Execute the complete Power BI data model pipeline"""
    print("🚀 Starting Power BI Data Model Pipeline")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Step 1: Load and validate data
        print("\n📊 Step 1: Loading and validating data...")
        from data_loader import load_survey_data, validate_data, identify_open_ended_columns
        df = load_survey_data()
        if df is None:
            raise Exception("Failed to load survey data")
        
        validation = validate_data(df)
        open_ended_cols = identify_open_ended_columns(df)
        print(f"   ✅ Data loaded: {validation['total_responses']} responses")
        print(f"   ✅ Open-ended questions: {len(open_ended_cols)}")
        
        # Step 2: Process text responses
        print("\n🔧 Step 2: Processing text responses...")
        from text_processing import batch_process_responses
        processed_responses = batch_process_responses(df, open_ended_cols[:8])  # Process more open-ended questions
        print(f"   ✅ Processed {len(processed_responses)} response records")
        
        # Step 3: Create dimension tables
        print("\n🏗️ Step 3: Creating dimension tables...")
        
        # Healthcare Category Dimension
        from dim_healthcare_category import create_healthcare_category_dimension
        dim_healthcare_category = create_healthcare_category_dimension()
        print(f"   ✅ DimHealthcareCategory: {len(dim_healthcare_category)} records")
        
        # Geography Dimension
        from dim_geography import create_geography_dimension
        dim_geography = create_geography_dimension(df)
        print(f"   ✅ DimGeography: {len(dim_geography)} records")
        
        # Organization Dimension
        from dim_organization import create_organization_dimension
        dim_organization = create_organization_dimension(df)
        print(f"   ✅ DimOrganization: {len(dim_organization)} records")
        
        # Urgency Dimension
        from dim_urgency import create_urgency_dimension
        dim_urgency = create_urgency_dimension()
        print(f"   ✅ DimUrgency: {len(dim_urgency)} records")
        
        # Question Dimension
        from dim_question import create_question_dimension
        dim_question = create_question_dimension(df)
        print(f"   ✅ DimQuestion: {len(dim_question)} records")
        
        # Role Dimension
        from dim_role import create_role_dimension
        dim_role = create_role_dimension(df)
        print(f"   ✅ DimRole: {len(dim_role)} records")
        
        # Tag Dimension (for individual response phrase analysis)
        from dim_tags_individual import create_tag_dimension, create_individual_response_tag_bridge
        dim_tags = create_tag_dimension()
        print(f"   ✅ DimTags: {len(dim_tags)} records")
        
        # Step 4: Create fact table
        print("\n📋 Step 4: Creating fact table...")
        from fact_survey_responses import create_fact_table
        fact_table = create_fact_table(df, dim_geography, dim_organization, 
                                     dim_urgency, dim_question, dim_role)
        print(f"   ✅ FactSurveyResponses: {len(fact_table)} records")
        
        # Step 5: Create bridge tables
        print("\n🔗 Step 5: Creating bridge tables...")
        from bridge_tables import create_bridge_tables
        bridge_categories, bridge_roles = create_bridge_tables(processed_responses, dim_healthcare_category)
        print(f"   ✅ BridgeResponseCategories: {len(bridge_categories)} records")
        print(f"   ✅ BridgeResponseRoles: {len(bridge_roles)} records")
        
        # Create tag bridge table for individual response analysis
        bridge_tags = create_individual_response_tag_bridge(fact_table, dim_tags)
        print(f"   ✅ BridgeResponseTags: {len(bridge_tags)} records")
        
        # Step 6: Export to CSV
        print("\n📁 Step 6: Exporting to CSV files...")
        from export_csvs import export_all_tables
        
        tables = {
            'DimHealthcareCategory': dim_healthcare_category,
            'DimGeography': dim_geography,
            'DimOrganization': dim_organization,
            'DimRole': dim_role,
            'DimUrgency': dim_urgency,
            'DimQuestion': dim_question,
            'DimTags': dim_tags,
            'FactSurveyResponses': fact_table,
            'BridgeResponseCategories': bridge_categories,
            'BridgeResponseRoles': bridge_roles,
            'BridgeResponseTags': bridge_tags
        }
        
        exported_files = export_all_tables(tables)
        print(f"   ✅ Exported {len(exported_files)} CSV files")
        
        # Pipeline completion
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"⏱️ Total execution time: {elapsed_time:.1f} seconds")
        print(f"📂 Files exported to: powerbi_data_model/")
        print("\n💡 Next step: Import CSV files into Power BI Desktop")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
