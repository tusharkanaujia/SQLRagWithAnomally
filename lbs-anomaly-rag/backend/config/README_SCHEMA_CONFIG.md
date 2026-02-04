# Schema Configuration Guide

## Overview

The schema configuration system provides an easy, maintainable way to define your database schema for the RAG system. Instead of hardcoding schema information in Python strings, you configure it in a structured JSON file.

## Files

1. **[schema_config.json](schema_config.json)** - Main configuration file containing fact tables, dimension tables, and business rules
2. **[schema_manager.py](schema_manager.py)** - Python module that loads and processes the configuration
3. **[../services/schema_context.py](../services/schema_context.py)** - Updated to use the schema manager

## Benefits

✅ **Easy to Maintain** - Edit JSON instead of Python code
✅ **Structured** - Clear organization of tables, columns, and relationships
✅ **Validatable** - JSON schema can be validated
✅ **Extensible** - Easy to add new tables or databases
✅ **Auto-Documentation** - Schema context is generated automatically
✅ **Version Control** - Track schema changes over time

## How to Add/Modify Tables

### Adding a New Dimension Table

Edit `schema_config.json` and add to the `dimension_tables` array:

```json
{
  "name": "DimEmployee",
  "alias": "emp",
  "description": "Employee information",
  "row_count": 296,
  "primary_key": {"name": "EmployeeKey", "type": "int"},
  "columns": [
    {"name": "EmployeeNationalIDAlternateKey", "type": "nvarchar(15)", "description": "Employee ID", "business_key": true},
    {"name": "FirstName", "type": "nvarchar(50)", "description": "First name"},
    {"name": "LastName", "type": "nvarchar(50)", "description": "Last name"},
    {"name": "Title", "type": "nvarchar(50)", "description": "Job title"},
    {"name": "BirthDate", "type": "date", "description": "Birth date"},
    {"name": "HireDate", "type": "date", "description": "Hire date"}
  ]
}
```

### Adding a New Fact Table

Add to the `fact_tables` array:

```json
{
  "name": "FactResellerSales",
  "alias": "resel",
  "description": "Reseller sales transactions",
  "row_count": 60855,
  "primary_keys": [
    {"name": "SalesOrderNumber", "type": "nvarchar(20)"},
    {"name": "SalesOrderLineNumber", "type": "tinyint"}
  ],
  "foreign_keys": [
    {"name": "ProductKey", "type": "int", "references": "DimProduct.ProductKey"},
    {"name": "ResellerKey", "type": "int", "references": "DimReseller.ResellerKey"},
    {"name": "OrderDateKey", "type": "int", "references": "DimDate.DateKey"}
  ],
  "measures": [
    {"name": "SalesAmount", "type": "money", "description": "Total sales amount", "aggregation": "SUM"},
    {"name": "OrderQuantity", "type": "smallint", "description": "Quantity ordered", "aggregation": "SUM"}
  ]
}
```

### Modifying Existing Tables

Simply edit the JSON entry for that table. For example, to add a new column:

```json
{
  "name": "DimCustomer",
  "columns": [
    ...existing columns...,
    {"name": "LoyaltyTier", "type": "nvarchar(20)", "description": "Customer loyalty tier"}
  ]
}
```

## Schema Structure Reference

### Fact Table Structure

```json
{
  "name": "TableName",                 // Required: Table name
  "alias": "alias",                    // Required: Short alias for queries
  "description": "Description",        // Required: Table description
  "row_count": 0,                      // Required: Approximate row count
  "primary_keys": [...],               // Optional: Primary key columns
  "foreign_keys": [...],               // Optional: Foreign key relationships
  "measures": [...],                   // Optional: Numeric measures/metrics
  "attributes": [...]                  // Optional: Other attributes
}
```

### Dimension Table Structure

```json
{
  "name": "DimTableName",              // Required: Table name
  "alias": "alias",                    // Required: Short alias for queries
  "description": "Description",        // Required: Table description
  "row_count": 0,                      // Required: Approximate row count
  "primary_key": {...},                // Required: Primary key
  "columns": [...],                    // Required: All columns
  "date_range": {...},                 // Optional: For date dimensions
  "name_concatenation": "...",         // Optional: How to build full name
  "special_notes": "..."               // Optional: Special notes
}
```

### Column Definition

```json
{
  "name": "ColumnName",                // Required: Column name
  "type": "datatype",                  // Required: SQL data type
  "description": "Description",        // Required: What this column contains
  "values": ["A", "B"],                // Optional: Valid values (for enums)
  "business_key": true,                // Optional: Mark as business key
  "aggregation": "SUM"                 // Optional: Default aggregation (for measures)
}
```

## Business Rules

Add business rules to help the LLM generate better SQL:

```json
{
  "business_rules": [
    {
      "rule": "unique_rule_name",
      "description": "Description of the rule for the LLM"
    }
  ]
}
```

## Common Aggregations

Define common metric calculations:

```json
{
  "common_aggregations": {
    "sales_metrics": [
      "SUM(SalesAmount)",
      "COUNT(DISTINCT OrderNumber)",
      "AVG(SalesAmount)"
    ],
    "customer_metrics": [
      "COUNT(DISTINCT CustomerKey)",
      "SUM(TotalPurchases)"
    ]
  }
}
```

## Using the Schema Manager in Code

### Get Schema Context for LLM

```python
from services.schema_context import get_schema_context

# Get formatted schema text for LLM
schema_text = get_schema_context()
```

### Get Table Information

```python
from config.schema_manager import get_schema_manager

manager = get_schema_manager()

# Get all tables
fact_tables = manager.get_fact_tables()
dim_tables = manager.get_dimension_tables()

# Get specific table info
customer_table = manager.get_table_by_name('DimCustomer')

# Get column list
columns = manager.get_column_list('FactInternetSales')
```

### Get Table Lists

```python
from services.schema_context import get_table_list, get_fact_tables, get_dimension_tables

# All tables
all_tables = get_table_list()

# Just fact tables
facts = get_fact_tables()

# Just dimension tables
dimensions = get_dimension_tables()
```

## Testing the Configuration

Test that your configuration loads correctly:

```bash
cd backend
python -c "from config.schema_manager import get_schema_manager; sm = get_schema_manager(); print('Tables:', sm.get_table_list()); print('Schema loaded successfully!')"
```

Generate schema context to verify format:

```bash
python -c "from services.schema_context import get_schema_context; print(get_schema_context())"
```

## Advanced: Multiple Databases

To support multiple databases, create separate config files:

```
config/
  ├── schema_config.json              # Default (AdventureWorks)
  ├── schema_config_northwind.json    # Northwind database
  └── schema_config_custom.json       # Your custom database
```

Then specify which to load:

```python
from config.schema_manager import SchemaManager

# Load specific config
manager = SchemaManager('config/schema_config_northwind.json')
```

## Best Practices

1. **Keep row counts updated** - Helps LLM understand data volume
2. **Add descriptions** - Clear descriptions improve SQL generation
3. **Document special values** - List valid enum values
4. **Include business keys** - Mark alternate keys for better queries
5. **Specify aggregations** - Tell LLM how to aggregate measures
6. **Add business rules** - Document important query patterns
7. **Use consistent aliases** - Short, meaningful table aliases
8. **Version control** - Commit schema changes with descriptive messages

## Troubleshooting

**Error: "FileNotFoundError: schema_config.json"**
- Ensure the file exists in `backend/config/` directory
- Check file permissions

**Error: "JSONDecodeError"**
- Validate JSON syntax at [jsonlint.com](https://jsonlint.com)
- Check for trailing commas (not allowed in JSON)
- Ensure proper quote escaping

**Schema changes not reflected**
- Restart the backend server
- Check that you're editing the correct config file
- Clear Python cache: `rm -rf __pycache__`

## Example: Full Configuration Snippet

```json
{
  "database": "AdventureWorksDW2019",
  "description": "Internet Sales Data Warehouse",

  "fact_tables": [{
    "name": "FactInternetSales",
    "alias": "sal",
    "description": "Internet sales transactions",
    "row_count": 60398,
    "measures": [
      {"name": "SalesAmount", "type": "money", "description": "Sales amount", "aggregation": "SUM"}
    ]
  }],

  "dimension_tables": [{
    "name": "DimCustomer",
    "alias": "cust",
    "description": "Customer information",
    "row_count": 18484,
    "primary_key": {"name": "CustomerKey", "type": "int"},
    "columns": [
      {"name": "FirstName", "type": "nvarchar(50)", "description": "First name"}
    ]
  }],

  "business_rules": [
    {"rule": "date_joins", "description": "Always join dates using DateKey"}
  ]
}
```

## Need Help?

- Check existing examples in `schema_config.json`
- Review the SchemaManager class in `schema_manager.py`
- Test changes incrementally
- Use version control to track changes
