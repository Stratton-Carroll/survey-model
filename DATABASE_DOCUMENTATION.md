# Healthcare Survey Analysis Database Documentation

## Overview

This database powers a comprehensive healthcare survey analysis system with hierarchical tagging, multiple data layers, and manual override capabilities. The system is designed for iterative analysis where expert knowledge can refine algorithmic results.

## Database Architecture

### Core Tables

#### **1. FactSurveyResponses** (Main Data)
```sql
ResponseID          INTEGER PRIMARY KEY  -- Unique identifier for each response
SurveyResponseNumber INTEGER            -- Order within each question
QuestionID          INTEGER             -- Links to DimQuestion
ResponseText        TEXT                -- The actual survey response
WordCount           INTEGER             -- Number of words in response
ResponseLength      INTEGER             -- Character count
HasResponse         BOOLEAN             -- Whether response has content
OrganizationID      INTEGER             -- Links to DimOrganization
GeographyID         INTEGER             -- Links to DimGeography
RoleID              INTEGER             -- Links to DimRole
```

#### **2. DimTags** (Hierarchical Tag Structure)
```sql
TagID               INTEGER PRIMARY KEY  -- Unique tag identifier
TagName             TEXT                -- Display name (e.g., "Career Ladder and Succession Planning")
TagCategory         TEXT                -- Category (Clinical, Financial, Workforce, etc.)
TagDescription      TEXT                -- Detailed description
TagLevel            INTEGER             -- 1 = Primary Tag, 2 = Sub-tag
ParentTagID         INTEGER             -- Links to parent tag (NULL for primary tags)
IsActive            BOOLEAN             -- Whether tag is currently used
```

**Hierarchy Example:**
```
Leadership Development (Primary, TagLevel=1, ParentTagID=NULL)
  ↳ Career Ladder and Succession Planning (Sub, TagLevel=2, ParentTagID=2)

Compensation & Incentives (Primary, TagLevel=1, ParentTagID=NULL)  
  ↳ Tuition Reimbursement and Education Cost (Sub, TagLevel=2, ParentTagID=3)
  ↳ Community Investment (Sub, TagLevel=2, ParentTagID=3)
```

### Data Layer Tables (Priority Order)

#### **3. BridgeResponseTags** (Layer 1: Algorithmic - Lowest Priority)
```sql
ResponseID          INTEGER             -- Links to FactSurveyResponses
TagID               INTEGER             -- Links to DimTags
```
- **Purpose**: Original keyword-based algorithmic tag assignments
- **Source**: Automated analysis of response text
- **Priority**: Lowest - can be overridden by question mappings or manual changes

#### **4. QuestionTagMappings** (Layer 2: Question-based - Medium Priority)
```sql
MappingID           INTEGER PRIMARY KEY
ResponseID          INTEGER             -- Links to FactSurveyResponses
TagID               INTEGER             -- Links to DimTags
TagType             TEXT                -- 'Primary' or 'Sub'
AssignmentType      TEXT                -- 'AUTOMATIC', 'CONDITIONAL', 'SUGGESTED'
AppliedBy           TEXT                -- Who created this mapping
AppliedDate         TEXT                -- When it was applied
IsActive            BOOLEAN             -- Whether mapping is active
```
- **Purpose**: Question-specific tag assignments imported from Excel
- **Source**: Subject matter expert analysis (tags_normalized.xlsx)
- **Priority**: Medium - overrides algorithmic but can be overridden manually
- **Count**: 712 active mappings across all responses

#### **5. ManualTagOverrides** (Layer 3: Manual - Highest Priority)
```sql
OverrideID          INTEGER PRIMARY KEY
ResponseID          INTEGER             -- Links to FactSurveyResponses  
SurveyResponseNumber INTEGER            -- For legacy compatibility
QuestionID          INTEGER             -- Question context
TagID               INTEGER             -- Links to DimTags
Action              TEXT                -- 'ADD' or 'REMOVE'
AppliedBy           TEXT                -- Who made the change
AppliedDate         TEXT                -- When change was made
Notes               TEXT                -- Optional explanation
IsActive            BOOLEAN             -- Whether override is active
```
- **Purpose**: Manual corrections and additions by subject matter experts
- **Source**: UI-based tag editor
- **Priority**: Highest - always takes precedence
- **Logic**: Latest action wins (chronological priority)

## Data Layer Priority System

### How Tag Resolution Works

The system uses a 3-layer priority model where **Manual Overrides** always win:

```sql
-- Simplified effective tags logic
WITH EffectiveTags AS (
    -- Start with all possible tag sources
    SELECT TagID, 'algorithmic' as Source, 0 as Priority 
    FROM BridgeResponseTags WHERE ResponseID = ?
    
    UNION ALL
    
    SELECT TagID, 'question-mapping' as Source, 1 as Priority
    FROM QuestionTagMappings WHERE ResponseID = ? AND IsActive = 1
    
    UNION ALL 
    
    SELECT TagID, 'manual' as Source, 2 as Priority  
    FROM ManualTagOverrides WHERE ResponseID = ? AND Action = 'ADD'
    
    -- Remove any tags that were manually removed
    EXCEPT tags where manual Action = 'REMOVE'
)
-- Return highest priority source for each tag
SELECT DISTINCT TagID FROM EffectiveTags
GROUP BY TagID
ORDER BY MAX(Priority) DESC
```

### Priority Examples

| Scenario | Algorithmic | Question Mapping | Manual Override | Final Result |
|----------|-------------|------------------|----------------|--------------|
| Tag exists in all layers | ✅ Present | ✅ Present | ✅ ADD | **Shows** (Manual wins) |
| Tag removed manually | ✅ Present | ✅ Present | ❌ REMOVE | **Hidden** (Manual wins) |
| Question mapping only | ❌ Absent | ✅ Present | - None | **Shows** (Question wins) |
| Algorithmic only | ✅ Present | ❌ Absent | - None | **Shows** (Algorithmic wins) |
| Manual add + remove + add | ✅ Present | - Any | ✅ ADD (latest) | **Shows** (Latest manual wins) |

## Database Usage Guide

### For Dashboard Development

#### **1. Getting Effective Tags for Analysis**
```sql
-- Get all effective tags for a response with source information
WITH LatestManualOverrides AS (
    SELECT TagID, Action,
           ROW_NUMBER() OVER (PARTITION BY TagID ORDER BY AppliedDate DESC) as rn
    FROM ManualTagOverrides 
    WHERE ResponseID = ? AND IsActive = 1
),
AllTagSources AS (
    SELECT bt.TagID, 'algorithmic' as Source, 0 as Priority
    FROM BridgeResponseTags bt
    LEFT JOIN LatestManualOverrides lmo ON bt.TagID = lmo.TagID AND lmo.rn = 1
    WHERE bt.ResponseID = ? AND (lmo.Action IS NULL OR lmo.Action != 'REMOVE')
    
    UNION ALL
    
    SELECT qtm.TagID, 'question-mapping' as Source, 1 as Priority
    FROM QuestionTagMappings qtm
    LEFT JOIN LatestManualOverrides lmo ON qtm.TagID = lmo.TagID AND lmo.rn = 1
    WHERE qtm.ResponseID = ? AND qtm.IsActive = 1 
          AND (lmo.Action IS NULL OR lmo.Action != 'REMOVE')
    
    UNION ALL
    
    SELECT lmo.TagID, 'manual' as Source, 2 as Priority
    FROM LatestManualOverrides lmo
    WHERE lmo.rn = 1 AND lmo.Action = 'ADD'
),
EffectiveTags AS (
    SELECT TagID, Source,
           ROW_NUMBER() OVER (PARTITION BY TagID ORDER BY Priority DESC) as rn
    FROM AllTagSources
)
SELECT et.TagID, t.TagName, t.TagCategory, t.TagLevel, 
       t.ParentTagID, et.Source
FROM EffectiveTags et
JOIN DimTags t ON et.TagID = t.TagID
WHERE t.IsActive = 1 AND et.rn = 1
ORDER BY t.TagLevel, t.TagName
```

#### **2. Tag Distribution Analysis**
```sql
-- Get tag usage across all responses
SELECT t.TagName, t.TagCategory, t.TagLevel,
       COUNT(DISTINCT art.ResponseID) as ResponseCount,
       COUNT(CASE WHEN art.Source = 'algorithmic' THEN 1 END) as AlgorithmicCount,
       COUNT(CASE WHEN art.Source = 'question-mapping' THEN 1 END) as QuestionMappingCount,
       COUNT(CASE WHEN art.Source = 'manual' THEN 1 END) as ManualCount
FROM (/* Use EffectiveTags CTE from above */) art
JOIN DimTags t ON art.TagID = t.TagID
GROUP BY t.TagID, t.TagName, t.TagCategory, t.TagLevel
ORDER BY ResponseCount DESC
```

#### **3. Hierarchical Analysis**
```sql
-- Get primary tags with their sub-tag counts
SELECT primary.TagName as PrimaryTag,
       primary.TagCategory,
       COUNT(DISTINCT sub.TagID) as SubTagCount,
       COUNT(DISTINCT er.ResponseID) as ResponseCount
FROM DimTags primary
LEFT JOIN DimTags sub ON primary.TagID = sub.ParentTagID
LEFT JOIN (/* EffectiveTags for primary */) er ON primary.TagID = er.TagID
WHERE primary.TagLevel = 1 AND primary.IsActive = 1
GROUP BY primary.TagID, primary.TagName, primary.TagCategory
ORDER BY ResponseCount DESC
```

#### **4. Geographic and Role Analysis**
```sql
-- Tag distribution by geography and role
SELECT g.PrimaryCounty, g.Region, r.RoleCategory,
       t.TagName, COUNT(*) as TagCount
FROM FactSurveyResponses f
JOIN DimGeography g ON f.GeographyID = g.GeographyID
JOIN DimRole r ON f.RoleID = r.RoleID
JOIN (/* EffectiveTags CTE */) et ON f.ResponseID = et.ResponseID
JOIN DimTags t ON et.TagID = t.TagID
WHERE t.IsActive = 1
GROUP BY g.PrimaryCounty, g.Region, r.RoleCategory, t.TagName
ORDER BY TagCount DESC
```

### For UI Development

#### **API Endpoints Available:**
- `GET /api/tags` - All tags with response counts and hierarchy info
- `GET /api/tags/available` - Hierarchical structure for tag editor
- `GET /api/responses/{id}/effective-tags` - Effective tags for a specific response
- `POST /api/responses/{id}/tags` - Add/remove tags manually
- `GET /api/questions/{id}/tag-distribution` - Tag distribution for a question

#### **Manual Override Workflow:**
1. User clicks "Edit Tags" on a response
2. System fetches current effective tags and available tags
3. User adds/removes tags through UI
4. System creates ManualTagOverride records with Action='ADD'/'REMOVE'
5. Effective tags immediately reflect the changes with highest priority

## Data Backup and Safety

### Automatic Backup System
- **ManualTagOverrides** - Backed up before any database rebuild
- **QuestionTagMappings** - Preserved during system updates  
- **Hierarchical DimTags** - Structure preserved with relationships
- **Timestamped backups** - Multiple restore points available

### Safety Features
- **Non-destructive updates** - Original data always preserved
- **Audit trail** - All manual changes tracked with user and timestamp
- **Rollback capability** - Can restore from any backup point
- **Data layer isolation** - Each layer operates independently

## Performance Optimization

### Indexes
```sql
-- Core performance indexes
CREATE INDEX idx_fact_response_id ON FactSurveyResponses(ResponseID);
CREATE INDEX idx_bridge_tags_response ON BridgeResponseTags(ResponseID);
CREATE INDEX idx_question_mappings_response ON QuestionTagMappings(ResponseID);
CREATE INDEX idx_manual_overrides_response ON ManualTagOverrides(ResponseID);
CREATE INDEX idx_tags_hierarchy ON DimTags(ParentTagID, TagLevel);
```

### Query Optimization Tips
- Always filter by `IsActive = 1` for current data
- Use the pre-built effective tags queries as CTEs
- Cache tag hierarchy relationships for UI performance  
- Use `ResponseID` as primary key for joins (not SurveyResponseNumber)

## Data Quality Guidelines

### Tag Management
- **Consistent naming** - Follow established tag name conventions
- **Proper hierarchy** - Ensure sub-tags have valid parent relationships
- **Category alignment** - Sub-tags should match parent tag categories
- **Active status** - Regularly review and deactivate unused tags

### Manual Override Best Practices
- **Add meaningful notes** - Explain why manual changes were made
- **Consistent user identification** - Use standardized "AppliedBy" values
- **Regular audits** - Review manual overrides for patterns and consistency
- **Documentation** - Keep track of major tagging decisions

## Future Enhancements

### Planned Features
- **Batch manual operations** - Apply same changes across multiple responses
- **Tag confidence scoring** - Track reliability of different tag sources
- **Advanced analytics** - Time-series analysis of tag usage patterns
- **Export capabilities** - Generate reports in multiple formats

### Scalability Considerations
- Database can handle 100K+ responses efficiently
- Hierarchical queries optimized for deep tag structures
- Manual override system designed for high-frequency updates
- Backup system scales with data growth

---

## Quick Reference

### Key Relationships
- **ResponseID** - Unique identifier across all tables
- **TagID** - Links to hierarchical tag structure
- **TagLevel** - 1 = Primary, 2 = Sub-tag
- **ParentTagID** - Creates hierarchy relationships

### Priority Rules
1. **Manual Override** (highest) - Always wins
2. **Question Mapping** (medium) - Expert-defined assignments  
3. **Algorithmic** (lowest) - Automated analysis

### Data Sources
- **Original**: BridgeResponseTags (algorithmic)
- **Imported**: QuestionTagMappings (tags_normalized.xlsx)
- **Manual**: ManualTagOverrides (UI-generated)

This database architecture provides a robust foundation for healthcare survey analysis with the flexibility to incorporate expert knowledge while maintaining data integrity and analytical capability.