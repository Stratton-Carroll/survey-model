# Power BI Tag Analysis Guide

## 🏷️ Creating Tag Tallies Like Your Chart

This guide shows you exactly how to recreate the tag analysis chart you showed me, using the dimensional model we've created.

## 📊 Key Tables for Tag Analysis

### 1. DimTags
Contains all possible tags/phrases:
- **TagID**: Unique identifier
- **TagName**: Display name (e.g., "Compensation Incentives")
- **TagCategory**: Grouping (Financial, Clinical, Wellness, etc.)
- **TagPriority**: Priority level (High, Medium, Low)

### 2. BridgeResponseTags
Links responses to tags (many-to-many):
- **ResponseID**: Links to FactSurveyResponses
- **TagID**: Links to DimTags
- **TagName**: Tag display name for convenience

### 3. FactSurveyResponses
Main response data with metrics

## 🎯 Step-by-Step: Creating Your Tag Tally Chart

### Step 1: Create the Basic Measure
```dax
Total Responses by Tag = 
CALCULATE(
    DISTINCTCOUNT(BridgeResponseTags[ResponseID])
)
```

### Step 2: Create a Horizontal Bar Chart
1. **Visualization**: Horizontal Bar Chart
2. **Y-Axis**: DimTags[TagName]
3. **X-Axis**: [Total Responses by Tag] measure
4. **Sort by**: [Total Responses by Tag] (descending)

### Step 3: Add Color Coding by Priority
```dax
Tag Priority Color = 
SWITCH(
    SELECTEDVALUE(DimTags[TagPriority]),
    "High", "#FF4444",
    "Medium", "#FFAA00", 
    "Low", "#4CAF50",
    "#CCCCCC"
)
```

Then use this measure in the **Data Colors** section.

### Step 4: Enhanced Measures for Analysis

#### Response Percentage
```dax
Tag Response Percentage = 
VAR TotalResponses = DISTINCTCOUNT(FactSurveyResponses[ResponseID])
VAR TagResponses = [Total Responses by Tag]
RETURN
DIVIDE(TagResponses, TotalResponses, 0) * 100
```

#### Tag Rank
```dax
Tag Rank = 
RANKX(
    ALL(DimTags[TagName]), 
    [Total Responses by Tag], 
    , 
    DESC
)
```

#### Top 10 Tags Filter
```dax
Top 10 Tags = IF([Tag Rank] <= 10, 1, 0)
```

## 📈 Advanced Tag Analysis Visuals

### 1. Tag Category Matrix
- **Rows**: DimTags[TagCategory]
- **Columns**: DimTags[TagName]
- **Values**: [Total Responses by Tag]

### 2. Priority vs Frequency Scatter Plot
- **X-Axis**: [Total Responses by Tag]
- **Y-Axis**: DimTags[TagPriority] (converted to numeric)
- **Size**: [Tag Response Percentage]
- **Legend**: DimTags[TagCategory]

### 3. Tag Trend Over Time
- **X-Axis**: DimTime[Date]
- **Y-Axis**: [Total Responses by Tag]
- **Legend**: DimTags[TagName] (filter to top 5)

### 4. Organization vs Tags Heatmap
- **Rows**: DimOrganization[OrganizationName]
- **Columns**: DimTags[TagName]
- **Values**: [Total Responses by Tag]
- **Color Saturation**: Based on values

## 🔍 Filtering and Slicing

### Key Slicers to Add:
1. **DimTags[TagCategory]** - Filter by tag category
2. **DimTags[TagPriority]** - Filter by priority level
3. **DimOrganization[OrganizationType]** - Filter by org type
4. **DimGeography[Region]** - Filter by geographic region
5. **DimUrgency[UrgencyLevel]** - Filter by response urgency

### Cross-Filtering Setup:
- All slicers should cross-filter the tag chart
- Enable bi-directional filtering between:
  - FactSurveyResponses ↔ BridgeResponseTags
  - BridgeResponseTags ↔ DimTags

## 📊 Sample Dashboard Layout

```
┌─────────────────┬─────────────────┐
│   Key Metrics   │   Tag Filters   │
│  Cards & KPIs   │    Slicers      │
├─────────────────┴─────────────────┤
│                                   │
│        TAG TALLY CHART            │
│     (Your main chart)             │
│                                   │
├─────────────────┬─────────────────┤
│  Tag Category   │   Organization  │
│     Matrix      │   vs Tags Heat  │
└─────────────────┴─────────────────┘
```

## 🎨 Formatting Tips

### Chart Formatting:
- **Data Labels**: Show values on bars
- **Color Theme**: Use your organization's colors
- **Title**: "Survey Response Tags by Frequency"
- **Y-Axis**: Format tag names (remove underscores)

### Conditional Formatting:
```dax
Tag Bar Color = 
VAR Responses = [Total Responses by Tag]
RETURN
SWITCH(
    TRUE(),
    Responses >= 20, "#1f77b4",  // Dark blue for high
    Responses >= 10, "#ff7f0e",  // Orange for medium  
    Responses >= 5,  "#2ca02c",  // Green for low
    "#d62728"                    // Red for very low
)
```

## 🔄 Dynamic Tag Analysis

### Create a Parameter for Top N
1. **Modeling** → **New Parameter**
2. **Name**: "Top N Tags"
3. **Data Type**: Whole Number
4. **Default**: 10
5. **Min**: 5, **Max**: 20

### Use in Measure:
```dax
Top N Tags Dynamic = 
VAR TopN = SELECTEDVALUE('Top N Tags'[Top N Tags Value], 10)
RETURN
IF([Tag Rank] <= TopN, 1, 0)
```

## 🎯 Key DAX Patterns for Tag Analysis

### 1. Tag Co-occurrence
```dax
Tag Co-occurrence = 
VAR CurrentTag = SELECTEDVALUE(DimTags[TagName])
RETURN
CALCULATE(
    DISTINCTCOUNT(BridgeResponseTags[ResponseID]),
    FILTER(
        BridgeResponseTags,
        BridgeResponseTags[TagName] <> CurrentTag
    )
)
```

### 2. Tag Penetration by Organization
```dax
Tag Penetration = 
DIVIDE(
    DISTINCTCOUNT(BridgeResponseTags[ResponseID]),
    DISTINCTCOUNT(FactSurveyResponses[ResponseID])
)
```

### 3. Average Tags per Response
```dax
Avg Tags per Response = 
DIVIDE(
    COUNTROWS(BridgeResponseTags),
    DISTINCTCOUNT(BridgeResponseTags[ResponseID])
)
```

## ✅ Validation Checklist

- [ ] Tag chart shows correct counts
- [ ] Filtering works across all visuals
- [ ] Colors represent priority levels
- [ ] Top N parameter functions properly
- [ ] Cross-filtering between tables works
- [ ] Data labels are readable
- [ ] Chart updates when slicers change

---

**🎉 Result**: You'll have the exact same tag tally functionality as your reference chart, plus much more advanced analysis capabilities!
