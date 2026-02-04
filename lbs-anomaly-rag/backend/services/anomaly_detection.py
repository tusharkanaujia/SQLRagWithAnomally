"""Anomaly Detection Service"""
import pyodbc
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from scipy import stats
from sklearn.ensemble import IsolationForest
from config.settings import settings


class AnomalyDetector:
    """Detect anomalies in data warehouse using multiple methods"""

    def __init__(self):
        self.zscore_threshold = 3.0
        self.iqr_multiplier = 1.5

    def _get_db_connection(self):
        """Get database connection"""
        conn_str = settings.get_db_connection_string()
        return pyodbc.connect(conn_str, timeout=settings.QUERY_TIMEOUT)

    def detect_time_series_anomalies(
        self,
        metric: str = "SalesAmount",
        granularity: str = "daily",
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """
        Detect time series anomalies in data

        Args:
            metric: Metric to analyze (SalesAmount, OrderQuantity, etc.)
            granularity: Time granularity (daily, weekly, monthly)
            lookback_days: Number of days to analyze

        Returns:
            Dictionary with anomalies and analysis
        """
        conn = self._get_db_connection()

        # Build time series query based on granularity
        if granularity == "daily":
            date_column = "dt.FullDateAlternateKey"
            group_by = "dt.FullDateAlternateKey"
        elif granularity == "weekly":
            date_column = "dt.CalendarYear, dt.WeekNumberOfYear"
            group_by = "dt.CalendarYear, dt.WeekNumberOfYear"
        elif granularity == "monthly":
            date_column = "dt.CalendarYear, dt.MonthNumberOfYear"
            group_by = "dt.CalendarYear, dt.MonthNumberOfYear"
        else:
            date_column = "dt.FullDateAlternateKey"
            group_by = "dt.FullDateAlternateKey"

        query = f"""
        SELECT
            {date_column} AS TimePeriod,
            SUM(sal.{metric}) AS MetricValue,
            COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount
        FROM dbo.FactInternetSales sal
        INNER JOIN dbo.DimDate dt ON dt.DateKey = sal.OrderDateKey
        WHERE dt.FullDateAlternateKey >= DATEADD(DAY, -{lookback_days}, GETDATE())
        GROUP BY {group_by}
        ORDER BY {date_column}
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return {"anomalies": [], "statistics": {}, "method": "time_series"}

        # Calculate statistics
        df['Mean'] = df['MetricValue'].mean()
        df['StdDev'] = df['MetricValue'].std()
        df['ZScore'] = (df['MetricValue'] - df['Mean']) / df['StdDev']

        # Moving average and standard deviation
        window = min(7, len(df) // 3)
        if window >= 2:
            df['MA'] = df['MetricValue'].rolling(window=window, center=True).mean()
            df['MA_Std'] = df['MetricValue'].rolling(window=window, center=True).std()
            df['UpperBound'] = df['MA'] + (2 * df['MA_Std'])
            df['LowerBound'] = df['MA'] - (2 * df['MA_Std'])
        else:
            df['MA'] = df['Mean']
            df['UpperBound'] = df['Mean'] + (2 * df['StdDev'])
            df['LowerBound'] = df['Mean'] - (2 * df['StdDev'])

        # Identify anomalies
        df['IsAnomaly'] = (
            (df['MetricValue'] > df['UpperBound']) |
            (df['MetricValue'] < df['LowerBound'])
        )

        # Extract anomalies
        anomalies = []
        for _, row in df[df['IsAnomaly']].iterrows():
            anomaly_type = "spike" if row['MetricValue'] > row['UpperBound'] else "drop"
            severity = "high" if abs(row['ZScore']) > 3 else "medium"

            anomalies.append({
                "time_period": str(row['TimePeriod']),
                "metric_value": float(row['MetricValue']),
                "expected_value": float(row['MA']),
                "deviation": float(row['MetricValue'] - row['MA']),
                "deviation_pct": float(((row['MetricValue'] - row['MA']) / row['MA'] * 100) if row['MA'] != 0 else 0),
                "zscore": float(row['ZScore']),
                "type": anomaly_type,
                "severity": severity,
                "order_count": int(row['OrderCount'])
            })

        statistics = {
            "total_periods": len(df),
            "anomaly_count": len(anomalies),
            "mean_value": float(df['MetricValue'].mean()),
            "std_dev": float(df['MetricValue'].std()),
            "min_value": float(df['MetricValue'].min()),
            "max_value": float(df['MetricValue'].max()),
            "granularity": granularity,
            "lookback_days": lookback_days
        }

        return {
            "anomalies": anomalies,
            "statistics": statistics,
            "method": "time_series",
            "time_series_data": df.to_dict('records')
        }

    def detect_statistical_anomalies(
        self,
        dimension: str = "ProductKey",
        metric: str = "SalesAmount",
        method: str = "zscore"
    ) -> Dict[str, Any]:
        """
        Detect statistical anomalies using Z-score or IQR

        Args:
            dimension: Dimension to analyze (ProductKey, CustomerKey, etc.)
            metric: Metric to analyze
            method: Detection method (zscore, iqr, isolation_forest)

        Returns:
            Dictionary with anomalies and analysis
        """
        conn = self._get_db_connection()

        # Map dimension to table and display column
        dimension_map = {
            "ProductKey": ("prod", "EnglishProductName", "DimProduct"),
            "CustomerKey": ("cust", "FirstName + ' ' + LastName", "DimCustomer"),
            "SalesTerritoryKey": ("st", "SalesTerritoryRegion", "DimSalesTerritory"),
            "PromotionKey": ("promo", "EnglishPromotionName", "DimPromotion")
        }

        if dimension not in dimension_map:
            dimension = "ProductKey"

        alias, display_col, dim_table = dimension_map[dimension]

        query = f"""
        SELECT
            sal.{dimension},
            {alias}.{display_col} AS DimensionName,
            SUM(sal.{metric}) AS MetricValue,
            COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount,
            AVG(sal.{metric}) AS AvgValue,
            MIN(sal.{metric}) AS MinValue,
            MAX(sal.{metric}) AS MaxValue
        FROM dbo.FactInternetSales sal
        INNER JOIN dbo.{dim_table} {alias} ON {alias}.{dimension} = sal.{dimension}
        GROUP BY sal.{dimension}, {alias}.{display_col}
        HAVING COUNT(DISTINCT sal.SalesOrderNumber) >= 5
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return {"anomalies": [], "statistics": {}, "method": method}

        anomalies = []

        if method == "zscore":
            # Z-score method
            mean = df['MetricValue'].mean()
            std = df['MetricValue'].std()
            df['ZScore'] = (df['MetricValue'] - mean) / std
            df['IsAnomaly'] = abs(df['ZScore']) > self.zscore_threshold

            for _, row in df[df['IsAnomaly']].iterrows():
                anomalies.append({
                    "dimension": dimension,
                    "dimension_value": str(row['DimensionName']),
                    "metric_value": float(row['MetricValue']),
                    "expected_value": float(mean),
                    "deviation": float(row['MetricValue'] - mean),
                    "zscore": float(row['ZScore']),
                    "severity": "high" if abs(row['ZScore']) > 4 else "medium",
                    "order_count": int(row['OrderCount'])
                })

        elif method == "iqr":
            # IQR method
            Q1 = df['MetricValue'].quantile(0.25)
            Q3 = df['MetricValue'].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - (self.iqr_multiplier * IQR)
            upper_bound = Q3 + (self.iqr_multiplier * IQR)

            df['IsAnomaly'] = (
                (df['MetricValue'] < lower_bound) |
                (df['MetricValue'] > upper_bound)
            )

            for _, row in df[df['IsAnomaly']].iterrows():
                anomalies.append({
                    "dimension": dimension,
                    "dimension_value": str(row['DimensionName']),
                    "metric_value": float(row['MetricValue']),
                    "expected_range": [float(lower_bound), float(upper_bound)],
                    "deviation": float(row['MetricValue'] - Q3 if row['MetricValue'] > upper_bound else Q1 - row['MetricValue']),
                    "severity": "high" if (row['MetricValue'] < lower_bound - IQR or row['MetricValue'] > upper_bound + IQR) else "medium",
                    "order_count": int(row['OrderCount'])
                })

        elif method == "isolation_forest":
            # Isolation Forest
            if len(df) >= 10:
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                df['Anomaly'] = iso_forest.fit_predict(df[['MetricValue']].values)
                df['IsAnomaly'] = df['Anomaly'] == -1

                median = df['MetricValue'].median()

                for _, row in df[df['IsAnomaly']].iterrows():
                    anomalies.append({
                        "dimension": dimension,
                        "dimension_value": str(row['DimensionName']),
                        "metric_value": float(row['MetricValue']),
                        "expected_value": float(median),
                        "deviation": float(row['MetricValue'] - median),
                        "severity": "medium",
                        "order_count": int(row['OrderCount'])
                    })

        statistics = {
            "total_items": len(df),
            "anomaly_count": len(anomalies),
            "mean_value": float(df['MetricValue'].mean()),
            "median_value": float(df['MetricValue'].median()),
            "std_dev": float(df['MetricValue'].std()),
            "min_value": float(df['MetricValue'].min()),
            "max_value": float(df['MetricValue'].max())
        }

        return {
            "anomalies": anomalies,
            "statistics": statistics,
            "method": method,
            "dimension": dimension
        }

    def detect_comparative_anomalies(
        self,
        comparison_type: str = "yoy",  # year-over-year, month-over-month, week-over-week
        metric: str = "SalesAmount",
        threshold_pct: float = 20.0
    ) -> Dict[str, Any]:
        """
        Detect anomalies by comparing current period to previous period

        Args:
            comparison_type: Type of comparison (yoy, mom, wow, qoq)
            metric: Metric to compare
            threshold_pct: Percentage threshold for anomaly

        Returns:
            Dictionary with comparative anomalies
        """
        conn = self._get_db_connection()

        if comparison_type == "yoy":
            # Year over Year
            query = f"""
            WITH YearlyData AS (
                SELECT
                    dt.CalendarYear,
                    dt.MonthNumberOfYear,
                    dt.EnglishMonthName,
                    SUM(sal.{metric}) AS MetricValue,
                    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount
                FROM dbo.FactInternetSales sal
                INNER JOIN dbo.DimDate dt ON dt.DateKey = sal.OrderDateKey
                GROUP BY dt.CalendarYear, dt.MonthNumberOfYear, dt.EnglishMonthName
            )
            SELECT
                curr.CalendarYear AS CurrentYear,
                curr.MonthNumberOfYear AS Month,
                curr.EnglishMonthName AS MonthName,
                curr.MetricValue AS CurrentValue,
                prev.MetricValue AS PreviousValue,
                curr.OrderCount AS CurrentOrders,
                prev.OrderCount AS PreviousOrders
            FROM YearlyData curr
            LEFT JOIN YearlyData prev
                ON curr.MonthNumberOfYear = prev.MonthNumberOfYear
                AND curr.CalendarYear = prev.CalendarYear + 1
            WHERE prev.MetricValue IS NOT NULL
            ORDER BY curr.CalendarYear, curr.MonthNumberOfYear
            """

        elif comparison_type == "mom":
            # Month over Month
            query = f"""
            WITH MonthlyData AS (
                SELECT
                    dt.CalendarYear,
                    dt.MonthNumberOfYear,
                    dt.EnglishMonthName,
                    SUM(sal.{metric}) AS MetricValue,
                    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount,
                    LAG(SUM(sal.{metric}), 1) OVER (ORDER BY dt.CalendarYear, dt.MonthNumberOfYear) AS PreviousValue,
                    LAG(COUNT(DISTINCT sal.SalesOrderNumber), 1) OVER (ORDER BY dt.CalendarYear, dt.MonthNumberOfYear) AS PreviousOrders
                FROM dbo.FactInternetSales sal
                INNER JOIN dbo.DimDate dt ON dt.DateKey = sal.OrderDateKey
                GROUP BY dt.CalendarYear, dt.MonthNumberOfYear, dt.EnglishMonthName
            )
            SELECT
                CalendarYear AS CurrentYear,
                MonthNumberOfYear AS Month,
                EnglishMonthName AS MonthName,
                MetricValue AS CurrentValue,
                PreviousValue,
                OrderCount AS CurrentOrders,
                PreviousOrders
            FROM MonthlyData
            WHERE PreviousValue IS NOT NULL
            ORDER BY CalendarYear, MonthNumberOfYear
            """

        elif comparison_type == "qoq":
            # Quarter over Quarter
            query = f"""
            WITH QuarterlyData AS (
                SELECT
                    dt.CalendarYear,
                    dt.CalendarQuarter,
                    SUM(sal.{metric}) AS MetricValue,
                    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount,
                    LAG(SUM(sal.{metric}), 1) OVER (ORDER BY dt.CalendarYear, dt.CalendarQuarter) AS PreviousValue,
                    LAG(COUNT(DISTINCT sal.SalesOrderNumber), 1) OVER (ORDER BY dt.CalendarYear, dt.CalendarQuarter) AS PreviousOrders
                FROM dbo.FactInternetSales sal
                INNER JOIN dbo.DimDate dt ON dt.DateKey = sal.OrderDateKey
                GROUP BY dt.CalendarYear, dt.CalendarQuarter
            )
            SELECT
                CalendarYear AS CurrentYear,
                CalendarQuarter AS Quarter,
                'Q' + CAST(CalendarQuarter AS VARCHAR) AS PeriodName,
                MetricValue AS CurrentValue,
                PreviousValue,
                OrderCount AS CurrentOrders,
                PreviousOrders
            FROM QuarterlyData
            WHERE PreviousValue IS NOT NULL
            ORDER BY CalendarYear, CalendarQuarter
            """

        else:
            raise ValueError(f"Unsupported comparison type: {comparison_type}")

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return {"anomalies": [], "statistics": {}, "method": "comparative"}

        # Calculate percentage change
        df['PercentChange'] = ((df['CurrentValue'] - df['PreviousValue']) / df['PreviousValue'] * 100)
        df['IsAnomaly'] = abs(df['PercentChange']) > threshold_pct

        anomalies = []
        for _, row in df[df['IsAnomaly']].iterrows():
            anomaly_type = "increase" if row['PercentChange'] > 0 else "decrease"
            severity = "high" if abs(row['PercentChange']) > threshold_pct * 2 else "medium"

            period_name = row.get('MonthName', row.get('PeriodName', str(row.get('CurrentYear'))))

            anomalies.append({
                "period": period_name,
                "year": int(row['CurrentYear']),
                "current_value": float(row['CurrentValue']),
                "previous_value": float(row['PreviousValue']),
                "change": float(row['CurrentValue'] - row['PreviousValue']),
                "percent_change": float(row['PercentChange']),
                "type": anomaly_type,
                "severity": severity,
                "current_orders": int(row['CurrentOrders']),
                "previous_orders": int(row.get('PreviousOrders', 0))
            })

        statistics = {
            "total_periods": len(df),
            "anomaly_count": len(anomalies),
            "avg_percent_change": float(df['PercentChange'].mean()),
            "max_increase": float(df['PercentChange'].max()),
            "max_decrease": float(df['PercentChange'].min()),
            "comparison_type": comparison_type
        }

        return {
            "anomalies": anomalies,
            "statistics": statistics,
            "method": "comparative",
            "comparison_data": df.to_dict('records')
        }

    def detect_day_on_day_anomalies(
        self,
        dimension: str = "ProductKey",
        metric: str = "SalesAmount",
        threshold_pct: float = 20.0,
        lookback_days: int = 30,
        top_n: int = 50
    ) -> Dict[str, Any]:
        """
        Detect day-on-day anomalies for a specific dimension

        Args:
            dimension: Dimension to analyze (ProductKey, CustomerKey, TerritoryKey, PromotionKey)
            metric: Metric to analyze (SalesAmount, OrderQuantity)
            threshold_pct: Minimum percent change to flag as anomaly
            lookback_days: Number of days to analyze
            top_n: Top N dimension values to analyze (by total metric value)

        Returns:
            Dictionary with day-on-day anomalies and analysis
        """
        conn = self._get_db_connection()

        # Map dimension to table and display columns
        dimension_config = {
            "ProductKey": {
                "table": "DimProduct",
                "join_key": "ProductKey",
                "name_column": "EnglishProductName",
                "category_column": "EnglishProductCategoryName"
            },
            "CustomerKey": {
                "table": "DimCustomer",
                "join_key": "CustomerKey",
                "name_column": "CONCAT(FirstName, ' ', LastName)",
                "category_column": "NULL"
            },
            "TerritoryKey": {
                "table": "DimSalesTerritory",
                "join_key": "SalesTerritoryKey",
                "name_column": "SalesTerritoryCountry",
                "category_column": "SalesTerritoryRegion"
            },
            "PromotionKey": {
                "table": "DimPromotion",
                "join_key": "PromotionKey",
                "name_column": "EnglishPromotionName",
                "category_column": "EnglishPromotionType"
            }
        }

        if dimension not in dimension_config:
            dimension = "ProductKey"

        dim_config = dimension_config[dimension]

        # Query to get top N dimension values and their daily metrics
        query = f"""
        WITH DailyMetrics AS (
            SELECT
                dt.FullDateAlternateKey AS Date,
                sal.{dim_config['join_key']} AS DimensionValue,
                SUM(sal.{metric}) AS MetricValue,
                COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount
            FROM dbo.FactInternetSales sal
            INNER JOIN dbo.DimDate dt ON dt.DateKey = sal.OrderDateKey
            WHERE dt.FullDateAlternateKey >= DATEADD(DAY, -{lookback_days}, GETDATE())
            GROUP BY dt.FullDateAlternateKey, sal.{dim_config['join_key']}
        ),
        TopDimensions AS (
            SELECT TOP {top_n}
                DimensionValue,
                SUM(MetricValue) AS TotalMetric
            FROM DailyMetrics
            GROUP BY DimensionValue
            ORDER BY SUM(MetricValue) DESC
        ),
        DoDCalculation AS (
            SELECT
                dm.Date,
                dm.DimensionValue,
                dm.MetricValue AS CurrentValue,
                dm.OrderCount AS CurrentOrders,
                LAG(dm.MetricValue) OVER (PARTITION BY dm.DimensionValue ORDER BY dm.Date) AS PreviousValue,
                LAG(dm.OrderCount) OVER (PARTITION BY dm.DimensionValue ORDER BY dm.Date) AS PreviousOrders,
                LAG(dm.Date) OVER (PARTITION BY dm.DimensionValue ORDER BY dm.Date) AS PreviousDate
            FROM DailyMetrics dm
            INNER JOIN TopDimensions td ON dm.DimensionValue = td.DimensionValue
        )
        SELECT
            dod.Date,
            dod.DimensionValue,
            dim.{dim_config['name_column']} AS DimensionName,
            {dim_config['category_column']} AS Category,
            dod.CurrentValue,
            dod.PreviousValue,
            dod.PreviousDate,
            dod.CurrentOrders,
            dod.PreviousOrders,
            CASE
                WHEN dod.PreviousValue > 0
                THEN ((dod.CurrentValue - dod.PreviousValue) / dod.PreviousValue) * 100
                ELSE NULL
            END AS PercentChange,
            dod.CurrentValue - dod.PreviousValue AS AbsoluteChange
        FROM DoDCalculation dod
        INNER JOIN dbo.{dim_config['table']} dim ON dim.{dim_config['join_key']} = dod.DimensionValue
        WHERE dod.PreviousValue IS NOT NULL
        ORDER BY dod.Date DESC, ABS((dod.CurrentValue - dod.PreviousValue) / NULLIF(dod.PreviousValue, 1)) DESC
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return {
                "anomalies": [],
                "statistics": {},
                "method": "day_on_day",
                "dimension": dimension
            }

        # Identify anomalies based on threshold
        df['IsAnomaly'] = df['PercentChange'].abs() >= threshold_pct

        # Extract anomalies
        anomalies = []
        for _, row in df[df['IsAnomaly']].iterrows():
            # Determine anomaly type and severity
            pct_change = float(row['PercentChange'])
            anomaly_type = "spike" if pct_change > 0 else "drop"

            if abs(pct_change) >= 50:
                severity = "high"
            elif abs(pct_change) >= 30:
                severity = "medium"
            else:
                severity = "low"

            # Generate natural language description
            dimension_label = {
                "ProductKey": "Product",
                "CustomerKey": "Customer",
                "TerritoryKey": "Territory",
                "PromotionKey": "Promotion"
            }.get(dimension, dimension)

            metric_label = "sales" if metric == "SalesAmount" else "order quantity"
            change_direction = "increased" if pct_change > 0 else "decreased"
            severity_text = severity.upper() if severity == "high" else severity.capitalize()

            # Build the natural language summary
            nl_description = (
                f"{severity_text} severity {anomaly_type} detected for {dimension_label} "
                f"'{row['DimensionName']}' on {str(row['Date'])}. "
                f"The {metric_label} {change_direction} by {abs(pct_change):.1f}% "
                f"from {row['PreviousValue']:,.0f} to {row['CurrentValue']:,.0f} "
                f"compared to the previous day ({str(row['PreviousDate'])})."
            )

            # Add category info if available
            if row['Category'] is not None and pd.notna(row['Category']):
                nl_description += f" Category: {row['Category']}."

            anomaly = {
                "date": str(row['Date']),
                "previous_date": str(row['PreviousDate']),
                "dimension_value": int(row['DimensionValue']),
                "dimension_name": str(row['DimensionName']),
                "current_value": float(row['CurrentValue']),
                "previous_value": float(row['PreviousValue']),
                "absolute_change": float(row['AbsoluteChange']),
                "percent_change": pct_change,
                "type": anomaly_type,
                "severity": severity,
                "current_orders": int(row['CurrentOrders']),
                "previous_orders": int(row['PreviousOrders']),
                "description": nl_description
            }

            if row['Category'] is not None and pd.notna(row['Category']):
                anomaly["category"] = str(row['Category'])

            anomalies.append(anomaly)

        # Calculate statistics
        statistics = {
            "total_comparisons": len(df),
            "anomaly_count": len(anomalies),
            "avg_percent_change": float(df['PercentChange'].mean()),
            "max_increase": float(df['PercentChange'].max()),
            "max_decrease": float(df['PercentChange'].min()),
            "dimension": dimension,
            "metric": metric,
            "threshold_pct": threshold_pct,
            "lookback_days": lookback_days,
            "top_n": top_n,
            "spike_count": len([a for a in anomalies if a['type'] == 'spike']),
            "drop_count": len([a for a in anomalies if a['type'] == 'drop'])
        }

        return {
            "anomalies": anomalies,
            "statistics": statistics,
            "method": "day_on_day",
            "all_data": df.to_dict('records')
        }

    def detect_prophet_anomalies(
        self,
        metric: str = "SalesAmount",
        lookback_days: int = 90,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Detect anomalies using Prophet forecasting with trend and seasonality

        This method uses Facebook Prophet to:
        - Automatically detect daily, weekly, and yearly seasonality
        - Identify trend changes
        - Flag values outside forecasted confidence intervals

        Args:
            metric: Metric to analyze (SalesAmount, OrderQuantity)
            lookback_days: Number of historical days to analyze
            forecast_days: Number of days to forecast into the future

        Returns:
            Dictionary with anomalies, forecast, and trend analysis
        """
        try:
            from prophet import Prophet
        except ImportError:
            return {
                "error": "Prophet not installed. Run: pip install prophet",
                "anomalies": [],
                "statistics": {}
            }

        conn = self._get_db_connection()

        # Get historical data
        query = f"""
        SELECT
            CAST(dt.FullDateAlternateKey AS DATE) AS Date,
            SUM(sal.{metric}) AS Value,
            COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount
        FROM FactInternetSales sal
        INNER JOIN DimDate dt ON dt.DateKey = sal.OrderDateKey
        WHERE dt.FullDateAlternateKey >= DATEADD(day, -{lookback_days}, GETDATE())
            AND dt.FullDateAlternateKey < CAST(GETDATE() AS DATE)
        GROUP BY CAST(dt.FullDateAlternateKey AS DATE)
        ORDER BY Date
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if len(df) < 14:
            return {
                "error": f"Insufficient data: {len(df)} days (need at least 14)",
                "anomalies": [],
                "statistics": {}
            }

        # Prepare data for Prophet (requires 'ds' and 'y' columns)
        df_prophet = df.rename(columns={'Date': 'ds', 'Value': 'y'})

        # Train Prophet model
        model = Prophet(
            daily_seasonality=False,  # Not enough resolution for daily
            weekly_seasonality=True,
            yearly_seasonality=True if lookback_days >= 365 else False,
            changepoint_prior_scale=0.05,  # Flexibility of trend changes
            interval_width=0.95  # 95% confidence interval
        )

        # Fit model
        model.fit(df_prophet)

        # Make forecast (historical + future)
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)

        # Detect anomalies (actual values outside confidence interval)
        anomalies = []

        for i, row in df_prophet.iterrows():
            date = row['ds']
            actual = row['y']

            # Get forecast for this date
            forecast_row = forecast[forecast['ds'] == date]

            if not forecast_row.empty:
                predicted = forecast_row.iloc[0]['yhat']
                lower_bound = forecast_row.iloc[0]['yhat_lower']
                upper_bound = forecast_row.iloc[0]['yhat_upper']
                trend = forecast_row.iloc[0]['trend']

                # Check if anomaly
                is_anomaly = actual < lower_bound or actual > upper_bound

                if is_anomaly:
                    deviation_pct = ((actual - predicted) / predicted) * 100 if predicted != 0 else 0

                    # Determine type and severity
                    if actual > upper_bound:
                        anomaly_type = "spike"
                        severity = "high" if deviation_pct > 100 else "medium"
                    else:
                        anomaly_type = "drop"
                        severity = "high" if deviation_pct < -50 else "medium"

                    # Generate natural language description
                    if actual > predicted:
                        change_direction = "exceeded forecast"
                    else:
                        change_direction = "fell below forecast"

                    nl_description = (
                        f"{severity.capitalize()} severity {anomaly_type} detected on {str(date)}. "
                        f"The {metric} {change_direction} by {abs(deviation_pct):.1f}%. "
                        f"Actual: {actual:,.0f}, Forecasted: {predicted:,.0f} "
                        f"(95% confidence interval: {lower_bound:,.0f} - {upper_bound:,.0f}). "
                        f"Current trend: {trend:,.0f}."
                    )

                    anomaly = {
                        "date": str(date.date()),
                        "actual_value": float(actual),
                        "forecasted_value": float(predicted),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound),
                        "trend": float(trend),
                        "deviation_pct": float(deviation_pct),
                        "type": anomaly_type,
                        "severity": severity,
                        "description": nl_description
                    }

                    anomalies.append(anomaly)

        # Generate future forecast insights
        future_forecast = []
        future_data = forecast[forecast['ds'] > df_prophet['ds'].max()].head(forecast_days)

        for _, row in future_data.iterrows():
            future_forecast.append({
                "date": str(row['ds'].date()),
                "forecasted_value": float(row['yhat']),
                "lower_bound": float(row['yhat_lower']),
                "upper_bound": float(row['yhat_upper']),
                "trend": float(row['trend'])
            })

        # Calculate statistics
        statistics = {
            "total_days_analyzed": len(df),
            "anomaly_count": len(anomalies),
            "anomaly_rate_pct": round((len(anomalies) / len(df)) * 100, 2),
            "metric": metric,
            "lookback_days": lookback_days,
            "forecast_days": forecast_days,
            "spike_count": len([a for a in anomalies if a['type'] == 'spike']),
            "drop_count": len([a for a in anomalies if a['type'] == 'drop']),
            "avg_deviation_pct": round(
                sum(abs(a['deviation_pct']) for a in anomalies) / len(anomalies), 2
            ) if anomalies else 0,
            "model_components": {
                "has_weekly_seasonality": True,
                "has_yearly_seasonality": lookback_days >= 365,
                "trend_detected": True
            }
        }

        return {
            "anomalies": anomalies,
            "future_forecast": future_forecast,
            "statistics": statistics,
            "method": "prophet",
            "model_info": {
                "algorithm": "Prophet (Facebook)",
                "confidence_interval": "95%",
                "seasonality": "Weekly" + (", Yearly" if lookback_days >= 365 else ""),
                "description": "Forecasting-based anomaly detection with trend and seasonality"
            }
        }

    def detect_all_anomalies(self) -> Dict[str, Any]:
        """
        Run all anomaly detection methods and return comprehensive results

        Returns:
            Dictionary with results from all detection methods
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "anomaly_types": {}
        }

        try:
            # Time series anomalies
            results["anomaly_types"]["time_series_daily"] = self.detect_time_series_anomalies(
                granularity="daily",
                lookback_days=30
            )

            results["anomaly_types"]["time_series_monthly"] = self.detect_time_series_anomalies(
                granularity="monthly",
                lookback_days=365
            )

            # Statistical anomalies
            results["anomaly_types"]["statistical_products"] = self.detect_statistical_anomalies(
                dimension="ProductKey",
                method="zscore"
            )

            results["anomaly_types"]["statistical_customers"] = self.detect_statistical_anomalies(
                dimension="CustomerKey",
                method="isolation_forest"
            )

            # Comparative anomalies
            results["anomaly_types"]["comparative_yoy"] = self.detect_comparative_anomalies(
                comparison_type="yoy",
                threshold_pct=15.0
            )

            results["anomaly_types"]["comparative_mom"] = self.detect_comparative_anomalies(
                comparison_type="mom",
                threshold_pct=20.0
            )

            # Summary
            total_anomalies = sum(
                len(result.get("anomalies", []))
                for result in results["anomaly_types"].values()
            )

            results["summary"] = {
                "total_anomalies": total_anomalies,
                "detection_methods": len(results["anomaly_types"]),
                "status": "success"
            }

        except Exception as e:
            results["summary"] = {
                "status": "error",
                "error": str(e)
            }

        return results
