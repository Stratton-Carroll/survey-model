# Power BI Data Model Pipeline

A modular Python pipeline that transforms healthcare survey data into a dimensional model optimized for Power BI analysis.

## 🏗️ Architecture

This pipeline uses **individual Python modules** instead of a single notebook, making it:
- ✅ **Modular** - Each component is separate and focused
- ✅ **Maintainable** - Easy to debug and modify individual parts  
- ✅ **Reusable** - Components can be used independently
- ✅ **Testable** - Each module can be tested in isolation

## 📁 File Structure

```
powerbi_pipeline/
├── config.py                    # Configuration and constants
├── healthcare_taxonomy.py       # Healthcare categories and roles
├── data_loader.py              # Data loading and validation
├── text_processing.py          # NLP and tagging functions
├── dim_healthcare_category.py  # Healthcare category dimension
├── dim_geography.py            # Geography dimension  
├── dim_organization.py         # Organization dimension
├── dim_urgency.py              # Urgency dimension
├── dim_question.py             # Question dimension
├── fact_survey_responses.py    # Main fact table
├── bridge_tables.py            # Many-to-many bridge tables
├── export_csvs.py              # CSV export functionality
├── run_pipeline.py             # Main orchestrator
└── README.md                   # This file
```

## 🚀 Quick Start

### Run Complete Pipeline:
```bash
cd powerbi_pipeline
python run_pipeline.py
```

### Run Individual Modules:
```bash
# Test data loading
python data_loader.py

# Test text processing
python text_processing.py

# Test individual dimensions
python dim_healthcare_category.py
python dim_organization.py
```

## 📊 Output

The pipeline generates **8 CSV files** in `powerbi_data_model/`:

### Dimension Tables:
- `DimHealthcareCategory.csv` - Healthcare domain categories
- `DimGeography.csv` - Counties and regions
- `DimOrganization.csv` - Healthcare organizations
- `DimUrgency.csv` - Urgency levels
- `DimQuestion.csv` - Survey questions

### Fact Table:
- `FactSurveyResponses.csv` - Main response data with metrics

### Bridge Tables:
- `BridgeResponseCategories.csv` - Response-to-category links
- `BridgeResponseRoles.csv` - Response-to-role links

### Documentation:
- `PowerBI_Import_Instructions.txt` - Step-by-step import guide

## 🔧 Customization

### Adding New Healthcare Categories:
Edit `healthcare_taxonomy.py`:
```python
HEALTHCARE_CATEGORIES['new_category'] = {
    'keywords': ['keyword1', 'keyword2'],
    'description': 'Category description',
    'priority_weight': 0.8,
    'domain': 'Domain Name'
}
```

### Modifying Data Processing:
Edit `text_processing.py` to change:
- Keyword matching logic
- Priority scoring algorithm
- Urgency detection rules

### Adding New Dimensions:
1. Create `dim_new_dimension.py`
2. Add import and call in `run_pipeline.py`
3. Add to export dictionary in step 6

## 🧪 Testing

Each module can be tested individually:

```bash
# Test all modules
python -m pytest powerbi_pipeline/

# Test specific module
python powerbi_pipeline/data_loader.py
```

## 📈 Pipeline Flow

```
1. Load Data (data_loader.py)
     ↓
2. Process Text (text_processing.py)
     ↓
3. Create Dimensions (dim_*.py)
     ↓
4. Create Fact Table (fact_survey_responses.py)
     ↓
5. Create Bridge Tables (bridge_tables.py)
     ↓
6. Export CSVs (export_csvs.py)
```

## 🔗 Dependencies

```python
# Core dependencies
pandas>=1.5.0
openpyxl>=3.0.0

# Optional (for extended analysis)
numpy>=1.21.0
```

## ⚡ Performance

- **Execution time**: ~0.8 seconds for 67 survey responses
- **Memory usage**: Minimal (loads data in chunks)
- **Scalability**: Handles thousands of responses efficiently

## 🛠️ Configuration

Key settings in `config.py`:
- `DATA_FILE`: Path to Excel survey data
- `OUTPUT_DIR`: Where to save CSV files  
- `MAX_RESPONSE_TEXT_LENGTH`: Text truncation limit
- `EXCLUDE_PATTERNS`: Columns to skip in analysis

## 📋 Next Steps

1. **Import to Power BI**: Follow instructions in generated txt file
2. **Create Relationships**: Set up dimension-to-fact relationships
3. **Build Measures**: Use provided DAX formulas
4. **Design Dashboard**: Create visualizations using star schema

## 🤝 Contributing

To extend this pipeline:
1. Add new modules following the naming convention
2. Update `run_pipeline.py` to include new modules
3. Add configuration options to `config.py`
4. Test individual modules before integration

---

**🎯 Result**: A clean, professional dimensional model ready for advanced Power BI analytics!
