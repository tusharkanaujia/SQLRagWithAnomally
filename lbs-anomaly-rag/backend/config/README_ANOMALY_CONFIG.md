# Anomaly Detection Configuration Guide

## Overview

The anomaly detection configuration system allows you to easily configure:
- ✅ Which anomaly detection methods to use
- ✅ What dimensions to analyze (Product, Customer, Territory, etc.)
- ✅ Detection parameters (thresholds, lookback periods, etc.)
- ✅ Filters to apply (date ranges, value constraints, etc.)
- ✅ Notification settings and severity levels

## Files

1. **[anomaly_config.json](anomaly_config.json)** - Main configuration file
2. **[anomaly_config_manager.py](anomaly_config_manager.py)** - Python module to load and use the configuration

## Configuration Structure

The configuration is organized into detection types:

### 1. Time Series Detection

Detects anomalies over time using moving averages and standard deviation.

```json
{
  "time_series": {
    "enabled": true,
    "configurations": [
      {
        "name": "Daily Sales Anomalies",
        "enabled": true,
        "metric": "SalesAmount",
        "granularity": "daily",
        "lookback_days": 90,
        "window_size": 7,
        "threshold_std": 2.5
      }
    ]
  }
}
```

**Parameters:**
- `metric`: Column to analyze (SalesAmount, OrderQuantity, etc.)
- `granularity`: Time granularity (daily, weekly, monthly)
- `lookback_days`: How many days of history to analyze
- `window_size`: Moving average window (in periods)
- `threshold_std`: Standard deviations for anomaly threshold

### 2. Statistical Detection

Detects outliers using statistical methods (Z-Score, IQR, Isolation Forest).

```json
{
  "statistical": {
    "enabled": true,
    "configurations": [
      {
        "name": "Product Sales Outliers",
        "enabled": true,
        "dimension": "ProductKey",
        "dimension_name_column": "EnglishProductName",
        "dimension_table": "DimProduct",
        "metric": "SalesAmount",
        "method": "zscore",
        "threshold": 3.0,
        "min_transactions": 10,
        "filters": {
          "date_range_days": 365
        },
        "additional_columns": ["Color", "ProductLine"]
      }
    ]
  }
}
```

**Parameters:**
- `dimension`: Dimension key (ProductKey, CustomerKey, etc.)
- `dimension_name_column`: Column for display names
- `dimension_table`: Dimension table to join
- `metric`: Metric to analyze
- `method`: Detection method (zscore, iqr, isolation_forest)
- `threshold`: Anomaly threshold (method-specific)
- `min_transactions`: Minimum transactions required
- `additional_columns`: Extra columns to include in results

### 3. Comparative Detection

Compares periods (Year-over-Year, Month-over-Month, Quarter-over-Quarter).

```json
{
  "comparative": {
    "enabled": true,
    "configurations": [
      {
        "name": "Year-over-Year Sales Comparison",
        "enabled": true,
        "comparison_type": "yoy",
        "metric": "SalesAmount",
        "threshold_pct": 20.0,
        "min_value": 1000,
        "aggregation_level": "monthly"
      }
    ]
  }
}
```

**Parameters:**
- `comparison_type`: Type of comparison (yoy, mom, qoq)
- `metric`: Metric to compare
- `threshold_pct`: Percentage change threshold for anomalies
- `min_value`: Minimum value to consider (filters small values)
- `aggregation_level`: Aggregation level (monthly, quarterly)

### 4. Day-on-Day Detection

Compares each day to the previous day for specific dimensions.

```json
{
  "day_on_day": {
    "enabled": true,
    "configurations": [
      {
        "name": "Product Daily Sales Changes",
        "enabled": true,
        "dimension": "ProductKey",
        "dimension_name_column": "EnglishProductName",
        "dimension_table": "DimProduct",
        "metric": "SalesAmount",
        "threshold_pct": 50.0,
        "lookback_days": 30,
        "top_n": 50,
        "filters": {
          "product_status": "Current",
          "min_sales_amount": 100
        },
        "additional_columns": ["ProductLine", "Color"]
      }
    ]
  }
}
```

**Parameters:**
- `dimension`: Dimension to analyze
- `metric`: Metric to track (SalesAmount, OrderQuantity)
- `threshold_pct`: Percentage change threshold
- `lookback_days`: Days of history to analyze
- `top_n`: Top N dimension values to analyze (by total metric)
- `filters`: Custom filters to apply
- `additional_columns`: Extra info columns to include

### 5. Custom Rules

Define custom business logic for anomaly detection.

```json
{
  "custom_rules": {
    "enabled": true,
    "rules": [
      {
        "name": "High Value Transaction Alert",
        "enabled": true,
        "description": "Alert when single transaction exceeds threshold",
        "condition": "SalesAmount > 5000",
        "severity": "high",
        "dimensions_to_include": ["CustomerKey", "ProductKey"]
      }
    ]
  }
}
```

## How to Configure

### Example 1: Enable/Disable Detection Types

To disable a detection type, set `enabled: false`:

```json
{
  "time_series": {
    "enabled": false  // Disables all time series detection
  }
}
```

To disable a specific configuration:

```json
{
  "time_series": {
    "enabled": true,
    "configurations": [
      {
        "name": "Daily Sales Anomalies",
        "enabled": false  // Disables just this one
      }
    ]
  }
}
```

### Example 2: Add New Dimension Analysis

To analyze anomalies for a new dimension like Employees:

```json
{
  "day_on_day": {
    "configurations": [
      {
        "name": "Employee Sales Performance",
        "enabled": true,
        "dimension": "EmployeeKey",
        "dimension_name_column": "CONCAT(FirstName, ' ', LastName)",
        "dimension_table": "DimEmployee",
        "metric": "SalesAmount",
        "threshold_pct": 40.0,
        "lookback_days": 30,
        "top_n": 20,
        "filters": {
          "employee_status": "Active"
        },
        "additional_columns": ["Title", "HireDate"]
      }
    ]
  }
}
```

### Example 3: Adjust Sensitivity

Make detection more sensitive (detect more anomalies):

```json
{
  "time_series": {
    "configurations": [
      {
        "threshold_std": 2.0  // Lower = more sensitive (was 2.5)
      }
    ]
  },
  "day_on_day": {
    "configurations": [
      {
        "threshold_pct": 20.0  // Lower = more sensitive (was 50.0)
      }
    ]
  }
}
```

Make detection less sensitive (fewer anomalies):

```json
{
  "statistical": {
    "configurations": [
      {
        "threshold": 4.0  // Higher = less sensitive (was 3.0)
      }
    ]
  }
}
```

### Example 4: Apply Filters

Add date range filter:

```json
{
  "global_filters": {
    "date_range": {
      "enabled": true,
      "start_date": "2013-01-01",
      "end_date": "2013-12-31"
    }
  }
}
```

Add territory filter:

```json
{
  "global_filters": {
    "territories": {
      "enabled": true,
      "include": ["United States", "Canada"],
      "exclude": []
    }
  }
}
```

Add dimension-specific filters:

```json
{
  "day_on_day": {
    "configurations": [
      {
        "name": "High-Value Customer Changes",
        "filters": {
          "min_yearly_income": 100000,
          "house_owner_flag": "1",
          "total_children": 2
        }
      }
    ]
  }
}
```

## Using the Configuration in Code

### Get Enabled Detections

```python
from config.anomaly_config_manager import get_anomaly_config_manager

manager = get_anomaly_config_manager()

# Check what's enabled
if manager.is_day_on_day_enabled():
    configs = manager.get_day_on_day_configs()
    for config in configs:
        print(f"Analyzing {config['dimension']}: {config['name']}")
```

### Get Configuration for Specific Dimension

```python
# Get day-on-day config for products
product_config = manager.get_day_on_day_config('ProductKey')

if product_config:
    threshold = product_config['threshold_pct']
    lookback = product_config['lookback_days']
    print(f"Product config: {threshold}% threshold, {lookback} days")
```

### Validate Configuration

```python
from config.anomaly_config_manager import validate_anomaly_config

# Check for configuration errors
messages = validate_anomaly_config()
if messages:
    print("Configuration issues:")
    for msg in messages:
        print(f"  - {msg}")
else:
    print("Configuration is valid!")
```

### Get All Active Configurations

```python
manager = get_anomaly_config_manager()
all_detections = manager.get_all_enabled_detections()

print("Active detections:")
for detection_type, configs in all_detections.items():
    print(f"\n{detection_type.upper()}:")
    for config in configs:
        print(f"  - {config['name']}")
```

## Global Filters

Global filters apply to all detections:

```json
{
  "global_filters": {
    "date_range": {
      "enabled": true,
      "start_date": "2013-01-01",
      "end_date": "2013-12-31"
    },
    "territories": {
      "enabled": true,
      "include": ["United States"],
      "exclude": []
    },
    "products": {
      "enabled": true,
      "include_categories": ["Bikes", "Components"],
      "exclude_products": []
    }
  }
}
```

## Notification Settings

Configure how anomalies are reported:

```json
{
  "notification_settings": {
    "severity_thresholds": {
      "critical": {"enabled": true, "notification": "immediate"},
      "high": {"enabled": true, "notification": "immediate"},
      "medium": {"enabled": true, "notification": "daily_digest"},
      "low": {"enabled": false}
    },
    "channels": {
      "email": {
        "enabled": true,
        "recipients": ["data-team@company.com"]
      },
      "slack": {
        "enabled": true,
        "webhook_url": "https://hooks.slack.com/..."
      },
      "database": {
        "enabled": true,
        "table": "AnomalyAlerts"
      }
    }
  }
}
```

## Performance Settings

Optimize performance for large datasets:

```json
{
  "performance_settings": {
    "max_concurrent_detections": 5,
    "batch_size": 1000,
    "cache_results": true,
    "cache_ttl_minutes": 60
  }
}
```

## Testing Your Configuration

Test the configuration loads correctly:

```bash
cd backend
python -c "from config.anomaly_config_manager import get_anomaly_config_manager; manager = get_anomaly_config_manager(); print('Loaded successfully!'); print('Enabled detections:', list(manager.get_all_enabled_detections().keys()))"
```

Validate configuration:

```bash
python -c "from config.anomaly_config_manager import validate_anomaly_config; messages = validate_anomaly_config(); print('Valid!' if not messages else '\n'.join(messages))"
```

## Common Use Cases

### 1. Focus on High-Value Products

```json
{
  "day_on_day": {
    "configurations": [
      {
        "name": "Premium Product Monitoring",
        "dimension": "ProductKey",
        "filters": {
          "min_list_price": 1000,
          "product_line": "R"
        }
      }
    ]
  }
}
```

### 2. Monitor VIP Customers

```json
{
  "day_on_day": {
    "configurations": [
      {
        "name": "VIP Customer Activity",
        "dimension": "CustomerKey",
        "filters": {
          "min_yearly_income": 150000,
          "number_cars_owned": 3
        }
      }
    ]
  }
}
```

### 3. Territory-Specific Analysis

```json
{
  "statistical": {
    "configurations": [
      {
        "name": "US Territory Performance",
        "dimension": "SalesTerritoryKey",
        "filters": {
          "territory_country": "United States"
        }
      }
    ]
  }
}
```

## Best Practices

1. **Start Conservative** - Begin with higher thresholds, then tighten as needed
2. **Enable Gradually** - Start with one detection type, add more as you validate
3. **Use Filters** - Focus on what matters (high-value products, VIP customers, etc.)
4. **Monitor Performance** - Adjust batch sizes and caching for large datasets
5. **Version Control** - Track configuration changes with descriptive commit messages
6. **Test Changes** - Validate configuration after modifications
7. **Document Custom Rules** - Add clear descriptions for business logic
8. **Review Regularly** - Update thresholds based on observed patterns

## Troubleshooting

**Issue: No anomalies detected**
- Lower thresholds to be more sensitive
- Increase lookback_days to have more data
- Check that filters aren't too restrictive
- Verify data exists in the date range

**Issue: Too many anomalies**
- Increase thresholds to be less sensitive
- Add filters to focus on important dimensions
- Increase min_transactions or min_value thresholds

**Issue: Configuration not loading**
- Validate JSON syntax
- Check file permissions
- Restart backend server
- Look for validation error messages

**Issue: Performance is slow**
- Reduce lookback_days
- Decrease top_n values
- Enable caching
- Increase batch_size
- Reduce number of additional_columns

## Next Steps

1. Review current [anomaly_config.json](anomaly_config.json)
2. Adjust thresholds for your business needs
3. Add/remove detection configurations
4. Test with validation command
5. Restart backend to apply changes
6. Monitor results and fine-tune

For more help, see the [Schema Configuration Guide](README_SCHEMA_CONFIG.md) for related concepts.
