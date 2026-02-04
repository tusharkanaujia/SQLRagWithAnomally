"""Schema context for LLM-based SQL generation"""
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.schema_manager import get_schema_manager


def get_schema_context():
    """
    Return the schema context for RAG

    This now dynamically loads from schema_config.json
    making it easy to maintain and update
    """
    manager = get_schema_manager()
    return manager.generate_schema_context_text() + "\n\n" + manager.get_joins_text()


def get_example_queries():
    """Return example natural language queries and their SQL"""
    return [
        {
            "question": "What were the total sales in 2013?",
            "sql": """
SELECT SUM(sal.SalesAmount) AS TotalSales
FROM FactInternetSales sal
INNER JOIN DimDate dt ON dt.DateKey = sal.OrderDateKey
WHERE dt.CalendarYear = 2013
""",
            "intent": "aggregate_sales"
        },
        {
            "question": "Who are the top 10 customers by total purchases?",
            "sql": """
SELECT TOP 10
    cust.FirstName + ' ' + cust.LastName AS CustomerName,
    cust.EmailAddress,
    SUM(sal.SalesAmount) AS TotalPurchases,
    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount
FROM FactInternetSales sal
INNER JOIN DimCustomer cust ON cust.CustomerKey = sal.CustomerKey
GROUP BY cust.CustomerKey, cust.FirstName, cust.LastName, cust.EmailAddress
ORDER BY TotalPurchases DESC
""",
            "intent": "top_customers"
        },
        {
            "question": "What products sold the most in quantity?",
            "sql": """
SELECT TOP 10
    prod.EnglishProductName,
    SUM(sal.OrderQuantity) AS TotalQuantity,
    SUM(sal.SalesAmount) AS TotalRevenue
FROM FactInternetSales sal
INNER JOIN DimProduct prod ON prod.ProductKey = sal.ProductKey
GROUP BY prod.ProductKey, prod.EnglishProductName
ORDER BY TotalQuantity DESC
""",
            "intent": "product_analysis"
        },
        {
            "question": "Show sales by country",
            "sql": """
SELECT
    st.SalesTerritoryCountry,
    SUM(sal.SalesAmount) AS TotalSales,
    COUNT(DISTINCT sal.CustomerKey) AS CustomerCount,
    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount
FROM FactInternetSales sal
INNER JOIN DimSalesTerritory st ON st.SalesTerritoryKey = sal.SalesTerritoryKey
GROUP BY st.SalesTerritoryCountry
ORDER BY TotalSales DESC
""",
            "intent": "geographic_analysis"
        },
        {
            "question": "What were monthly sales trends in 2013?",
            "sql": """
SELECT
    dt.CalendarYear,
    dt.MonthNumberOfYear,
    dt.EnglishMonthName,
    SUM(sal.SalesAmount) AS MonthlySales,
    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount
FROM FactInternetSales sal
INNER JOIN DimDate dt ON dt.DateKey = sal.OrderDateKey
WHERE dt.CalendarYear = 2013
GROUP BY dt.CalendarYear, dt.MonthNumberOfYear, dt.EnglishMonthName
ORDER BY dt.MonthNumberOfYear
""",
            "intent": "time_series"
        },
        {
            "question": "Which promotions generated the most revenue?",
            "sql": """
SELECT TOP 10
    promo.EnglishPromotionName,
    promo.DiscountPct,
    SUM(sal.SalesAmount) AS Revenue,
    SUM(sal.DiscountAmount) AS TotalDiscounts,
    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount
FROM FactInternetSales sal
INNER JOIN DimPromotion promo ON promo.PromotionKey = sal.PromotionKey
WHERE promo.PromotionKey <> 1
GROUP BY promo.PromotionKey, promo.EnglishPromotionName, promo.DiscountPct
ORDER BY Revenue DESC
""",
            "intent": "promotion_effectiveness"
        },
        {
            "question": "What's the average order value by customer education level?",
            "sql": """
SELECT
    cust.EnglishEducation,
    COUNT(DISTINCT cust.CustomerKey) AS CustomerCount,
    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount,
    AVG(sal.SalesAmount) AS AvgOrderValue,
    SUM(sal.SalesAmount) AS TotalSales
FROM FactInternetSales sal
INNER JOIN DimCustomer cust ON cust.CustomerKey = sal.CustomerKey
WHERE cust.EnglishEducation IS NOT NULL
GROUP BY cust.EnglishEducation
ORDER BY TotalSales DESC
""",
            "intent": "customer_segmentation"
        },
        {
            "question": "Show sales comparison between fiscal years",
            "sql": """
SELECT
    dt.FiscalYear,
    dt.FiscalQuarter,
    SUM(sal.SalesAmount) AS QuarterSales
FROM FactInternetSales sal
INNER JOIN DimDate dt ON dt.DateKey = sal.OrderDateKey
GROUP BY dt.FiscalYear, dt.FiscalQuarter
ORDER BY dt.FiscalYear, dt.FiscalQuarter
""",
            "intent": "fiscal_analysis"
        }
    ]


def get_table_list():
    """Get list of all table names"""
    manager = get_schema_manager()
    return manager.get_table_list()


def get_column_list(table_name: str):
    """Get list of column names for a table"""
    manager = get_schema_manager()
    return manager.get_column_list(table_name)


def get_fact_tables():
    """Get list of fact tables"""
    manager = get_schema_manager()
    return [table['name'] for table in manager.get_fact_tables()]


def get_dimension_tables():
    """Get list of dimension tables"""
    manager = get_schema_manager()
    return [table['name'] for table in manager.get_dimension_tables()]
