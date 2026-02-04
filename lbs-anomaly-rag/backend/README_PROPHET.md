# Prophet Anomaly Detection Guide

## Overview

**Prophet** is an AI-powered forecasting library from Facebook/Meta that provides **advanced anomaly detection** with automatic trend and seasonality awareness.

### Why Prophet?

Traditional anomaly detection compares to averages:
```
❌ Simple: "Today's sales ($10,000) > Average ($8,000)" → Anomaly
```

Prophet understands context:
```
✅ Smart: "Monday typically has high sales due to weekly pattern.
          Forecasted: $9,500. Actual: $10,000. Within normal range." → NOT an anomaly
```

## 🎯 Key Features

1. **Automatic Seasonality Detection**
   - Weekly patterns (weekday vs weekend)
   - Yearly patterns (seasonal business cycles)
   - Monthly patterns (end-of-month spikes)

2. **Trend Awareness**
   - Detects if business is growing or declining
   - Adjusts expectations based on trend direction

3. **Forecasting**
   - Predicts next 30 days
   - Provides confidence intervals (95%)
   - Shows expected vs actual values

4. **Better Descriptions**
   - "Actual exceeded forecast by 25%"
   - "Value fell below 95% confidence interval"
   - "Trend shows 10% growth over period"

## Installation

```bash
# Install Prophet
pip install prophet

# For better performance (optional)
pip install pystan
```

## API Usage

### Endpoint

```bash
GET /anomalies/prophet
```

### Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `metric` | string | SalesAmount | - | Metric to analyze (SalesAmount, OrderQuantity) |
| `lookback_days` | int | 90 | 14-730 | Historical days to analyze (min 14 for pattern detection) |
| `forecast_days` | int | 30 | 1-90 | Days to forecast into future |

### Example Requests

#### Basic Request
```bash
GET http://localhost:8000/anomalies/prophet
```

#### With Parameters
```bash
GET http://localhost:8000/anomalies/prophet?metric=SalesAmount&lookback_days=180&forecast_days=60
```

### Response Format

```json
{
  "anomalies": [
    {
      "date": "2024-01-15",
      "actual_value": 125000.0,
      "forecasted_value": 95000.0,
      "lower_bound": 85000.0,
      "upper_bound": 105000.0,
      "trend": 92000.0,
      "deviation_pct": 31.58,
      "type": "spike",
      "severity": "medium",
      "description": "Medium severity spike detected on 2024-01-15. The SalesAmount exceeded forecast by 31.6%. Actual: 125,000, Forecasted: 95,000 (95% confidence interval: 85,000 - 105,000). Current trend: 92,000."
    }
  ],
  "future_forecast": [
    {
      "date": "2024-02-01",
      "forecasted_value": 98000.0,
      "lower_bound": 88000.0,
      "upper_bound": 108000.0,
      "trend": 93000.0
    }
  ],
  "statistics": {
    "total_days_analyzed": 90,
    "anomaly_count": 3,
    "anomaly_rate_pct": 3.33,
    "spike_count": 2,
    "drop_count": 1,
    "avg_deviation_pct": 28.5,
    "model_components": {
      "has_weekly_seasonality": true,
      "has_yearly_seasonality": false,
      "trend_detected": true
    }
  },
  "model_info": {
    "algorithm": "Prophet (Facebook)",
    "confidence_interval": "95%",
    "seasonality": "Weekly",
    "description": "Forecasting-based anomaly detection with trend and seasonality"
  },
  "cached": false
}
```

## Understanding the Results

### Anomaly Fields

- **actual_value**: The real measured value on that date
- **forecasted_value**: What Prophet predicted (expected value)
- **lower_bound / upper_bound**: 95% confidence interval
  - If actual < lower_bound → Drop anomaly
  - If actual > upper_bound → Spike anomaly
- **trend**: The underlying business trend (growth/decline direction)
- **deviation_pct**: How far actual deviated from forecast

### Severity Levels

- **High**: Deviation > 100% (spike) or < -50% (drop)
- **Medium**: Everything else outside confidence interval
- **Low**: (Not flagged - within normal range)

### Confidence Intervals

**95% confidence interval** means:
- 95% of normal values fall within [lower_bound, upper_bound]
- Only 5% of normal values fall outside
- Values outside are likely anomalies

## Use Cases

### 1. Detect Unusual Sales Days

```bash
GET /anomalies/prophet?metric=SalesAmount&lookback_days=90
```

**Finds:**
- Days with unusually high/low sales
- Accounts for weekly patterns (Monday vs Sunday)
- Accounts for trends (growth business expects higher sales over time)

### 2. Forecast Future Performance

```bash
GET /anomalies/prophet?forecast_days=60
```

**Returns:**
- Next 60 days of expected sales
- Confidence ranges
- Trend direction

**Use for:**
- Inventory planning
- Resource allocation
- Revenue forecasting

### 3. Long-Term Trend Analysis

```bash
GET /anomalies/prophet?lookback_days=365&forecast_days=90
```

**Provides:**
- Yearly seasonality detection
- Long-term trend identification
- Quarterly pattern recognition

## Comparison with Other Methods

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Prophet** | ✅ Automatic seasonality<br>✅ Trend aware<br>✅ Forecasting<br>✅ Interpretable | ❌ Slower (5-30s)<br>❌ Needs more data (14+ days) | Business metrics with patterns |
| **Day-on-Day** | ✅ Very fast<br>✅ Simple | ❌ No seasonality<br>❌ No trend awareness | Quick daily monitoring |
| **Statistical (Z-Score)** | ✅ Fast<br>✅ Works on dimensions | ❌ Assumes normal distribution<br>❌ No time awareness | Product/customer outliers |
| **Comparative (YoY)** | ✅ Simple to understand<br>✅ Business-friendly | ❌ Only year-over-year<br>❌ Misses intra-year patterns | Annual comparisons |

## Example: How Prophet Works

### Input Data (90 days)

```
Date       | Sales
-----------|-------
Mon Jan 1  | $85K
Tue Jan 2  | $72K
Wed Jan 3  | $68K
...        | ...
Sat Feb 10 | $95K  ← Is this anomalous?
```

### Prophet Analysis

1. **Detect Patterns:**
   - "Weekends typically have 20% higher sales"
   - "Overall trend: 2% growth per week"

2. **Forecast for Feb 10:**
   - Base trend: $75K
   - Weekend adjustment: +$15K
   - Forecasted: $90K
   - Confidence interval: $80K - $100K

3. **Evaluation:**
   - Actual: $95K
   - Within confidence interval ($80K - $100K)
   - **Result: NOT an anomaly** ✅

### Compare to Simple Average

Simple average would say:
- Average sales: $75K
- Feb 10: $95K (27% above average)
- **False positive**: Flagged as anomaly ❌

Prophet correctly recognizes this is normal for a weekend.

## Advanced Configuration

### Modify Sensitivity

Edit [anomaly_detection.py:648](services/anomaly_detection.py#L648):

```python
model = Prophet(
    changepoint_prior_scale=0.05,  # Default
    interval_width=0.95  # 95% confidence (default)
)
```

**Increase sensitivity** (more anomalies):
```python
interval_width=0.80  # 80% confidence (tighter bounds)
```

**Decrease sensitivity** (fewer anomalies):
```python
interval_width=0.99  # 99% confidence (wider bounds)
```

### Add Holiday Effects

```python
from prophet import Prophet
import pandas as pd

# Define holidays
holidays = pd.DataFrame({
    'holiday': 'christmas',
    'ds': pd.to_datetime(['2023-12-25', '2024-12-25']),
    'lower_window': -2,
    'upper_window': 2
})

model = Prophet(holidays=holidays)
```

### Customize Seasonality

```python
model = Prophet(
    daily_seasonality=False,
    weekly_seasonality=True,
    yearly_seasonality='auto'  # Auto-detect if enough data
)

# Add custom seasonality
model.add_seasonality(
    name='monthly',
    period=30.5,
    fourier_order=5
)
```

## Performance Considerations

### Speed

| Data Points | Processing Time | Memory |
|-------------|-----------------|--------|
| 30 days | ~3-5 seconds | <100 MB |
| 90 days | ~5-10 seconds | <150 MB |
| 365 days | ~10-30 seconds | <300 MB |

### Caching

Prophet results are **automatically cached for 1 hour**:
- First request: 5-30 seconds
- Subsequent requests (within 1 hour): <50ms ✨

Clear cache:
```bash
DELETE /cache/clear?cache_type=anomaly
```

### Optimization Tips

1. **Use appropriate lookback:**
   - Daily patterns: 30-90 days
   - Weekly patterns: 60-180 days
   - Yearly patterns: 365-730 days

2. **Don't over-forecast:**
   - Forecast 30-60 days for best accuracy
   - Beyond 90 days, confidence drops significantly

3. **Batch requests:**
   - Run Prophet detection once per hour
   - Cache and reuse results
   - Don't run on every user request

## Troubleshooting

### Error: "Prophet not installed"

```bash
pip install prophet

# If that fails, try:
pip install pystan
pip install prophet
```

### Error: "Insufficient data: X days (need at least 14)"

Prophet needs minimum 14 days of data to detect patterns.

**Solution:** Increase `lookback_days` parameter.

### Warning: "Disabling weekly seasonality"

Happens when < 2 weeks of data.

**Solution:** Use at least 30 days for reliable seasonality detection.

### Slow Performance

**Solutions:**
1. Check if result is cached (should be instant after first run)
2. Reduce `lookback_days` (less data = faster)
3. Run in background/batch instead of real-time

### Unexpected Anomalies

**Debug:**
1. Check `future_forecast` to see what Prophet expects
2. Look at `trend` to understand growth direction
3. Review `model_components` to see what patterns were detected

**Common causes:**
- Business growth → trend adjusts expectations upward
- Seasonality → certain days expected to be high/low
- Too sensitive → Reduce `interval_width` to 0.80

## Integration with Frontend

### Display Anomalies

```javascript
// Fetch Prophet anomalies
const response = await fetch('/anomalies/prophet?lookback_days=90');
const data = await response.json();

// Display each anomaly
data.anomalies.forEach(anomaly => {
  console.log(`${anomaly.date}: ${anomaly.description}`);
  console.log(`  Severity: ${anomaly.severity}`);
  console.log(`  Deviation: ${anomaly.deviation_pct.toFixed(1)}%`);
});
```

### Show Forecast Chart

```javascript
// Plot forecast vs actual
const chartData = data.future_forecast.map(day => ({
  date: day.date,
  forecasted: day.forecasted_value,
  lower: day.lower_bound,
  upper: day.upper_bound
}));

// Use Chart.js, Recharts, etc. to visualize
```

## Best Practices

1. **Start with 90 days** of lookback for balanced accuracy
2. **Cache results** - Prophet is slow, cache is fast
3. **Run periodically** - Once per hour is sufficient
4. **Combine methods** - Use Prophet for trends + day-on-day for real-time
5. **Review forecasts** - Check if future predictions make business sense
6. **Tune sensitivity** - Adjust confidence interval based on your needs
7. **Document patterns** - Note detected seasonality for business insights

## Next Steps

1. ✅ Install Prophet: `pip install prophet`
2. ✅ Test endpoint: `GET /anomalies/prophet`
3. ✅ Review anomalies and forecasts
4. ✅ Integrate with frontend dashboard
5. ✅ Set up hourly background job for detection
6. ✅ Monitor cache hit rate for performance

## Related Documentation

- [Anomaly Configuration](README_ANOMALY_CONFIG.md) - Configure Prophet settings
- [Performance Guide](README_PERFORMANCE.md) - Caching and optimization
- [Prophet Official Docs](https://facebook.github.io/prophet/) - Advanced features

Prophet provides the most accurate anomaly detection for business metrics with trends and seasonality!
