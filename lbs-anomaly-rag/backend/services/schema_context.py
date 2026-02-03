"""Schema context for LLM-based SQL generation"""

SALES_SCHEMA_CONTEXT = """
# AdventureWorksDW2019 - Internet Sales Data Warehouse Schema

## Overview
This is a star schema for analyzing internet sales data with dimensions for customers, products, dates, territories, currencies, and promotions.

## Fact Table

### FactInternetSales (60,398 rows)
Main fact table containing internet sales transactions.

**Primary Keys:**
- SalesOrderNumber (nvarchar(20)) + SalesOrderLineNumber (tinyint)

**Foreign Keys:**
- ProductKey (int) -> DimProduct.ProductKey
- CustomerKey (int) -> DimCustomer.CustomerKey
- OrderDateKey (int) -> DimDate.DateKey
- DueDateKey (int) -> DimDate.DateKey
- ShipDateKey (int) -> DimDate.DateKey
- SalesTerritoryKey (int) -> DimSalesTerritory.SalesTerritoryKey
- CurrencyKey (int) -> DimCurrency.CurrencyKey
- PromotionKey (int) -> DimPromotion.PromotionKey

**Measures (Metrics):**
- SalesAmount (money) - Total sales amount in transaction currency
- OrderQuantity (smallint) - Number of units ordered
- UnitPrice (money) - Price per unit
- ExtendedAmount (money) - Line item total before discount
- DiscountAmount (float) - Total discount applied
- UnitPriceDiscountPct (float) - Discount percentage
- TaxAmt (money) - Tax amount
- Freight (money) - Shipping cost
- ProductStandardCost (money) - Standard cost of product
- TotalProductCost (money) - Total product cost for line

**Other Columns:**
- OrderDate (datetime) - Order date
- DueDate (datetime) - Due date
- ShipDate (datetime) - Ship date
- CarrierTrackingNumber (nvarchar(25))
- CustomerPONumber (nvarchar(25))
- RevisionNumber (tinyint)

## Dimension Tables

### DimCustomer (18,484 rows)
Customer demographic and contact information.

**Primary Key:** CustomerKey (int)

**Important Columns:**
- CustomerAlternateKey (nvarchar(15)) - Customer ID
- FirstName, MiddleName, LastName (nvarchar(50))
- FullName: Use CONCAT or + to combine FirstName, ' ', LastName
- EmailAddress (nvarchar(50))
- Gender (nvarchar(1)) - 'M' or 'F'
- BirthDate (date)
- MaritalStatus (nchar(1)) - 'S' or 'M'
- YearlyIncome (money)
- TotalChildren (tinyint)
- NumberChildrenAtHome (tinyint)
- EnglishEducation (nvarchar(40)) - Education level
- EnglishOccupation (nvarchar(100)) - Job title
- HouseOwnerFlag (nchar(1)) - '0' or '1'
- NumberCarsOwned (tinyint)
- CommuteDistance (nvarchar(15))
- DateFirstPurchase (date)
- Phone (nvarchar(20))
- AddressLine1, AddressLine2 (nvarchar(120))

### DimProduct (606 rows)
Product catalog information.

**Primary Key:** ProductKey (int)

**Important Columns:**
- ProductAlternateKey (nvarchar(25)) - Product SKU
- EnglishProductName (nvarchar(50)) - Product name
- ProductSubcategoryKey (int) - Links to DimProductSubcategory
- Color (nvarchar(15))
- Size (nvarchar(50))
- SizeRange (nvarchar(50))
- Weight (float)
- StandardCost (money)
- ListPrice (money)
- DealerPrice (money)
- ProductLine (nchar(2)) - 'R', 'M', 'T', 'S'
- Class (nchar(2)) - 'L', 'M', 'H'
- Style (nchar(2)) - 'W', 'M', 'U'
- ModelName (nvarchar(50))
- EnglishDescription (nvarchar(400))
- Status (nvarchar(7)) - 'Current' or NULL
- StartDate, EndDate (datetime)

### DimDate (3,652 rows)
Date dimension for time-based analysis.

**Primary Key:** DateKey (int) - Format: YYYYMMDD (e.g., 20140101)

**Important Columns:**
- FullDateAlternateKey (date) - Actual date value
- DayNumberOfWeek (tinyint) - 1-7 (Monday=1)
- EnglishDayNameOfWeek (nvarchar(10))
- DayNumberOfMonth (tinyint) - 1-31
- DayNumberOfYear (smallint) - 1-366
- WeekNumberOfYear (tinyint) - 1-53
- EnglishMonthName (nvarchar(10))
- MonthNumberOfYear (tinyint) - 1-12
- CalendarQuarter (tinyint) - 1-4
- CalendarYear (smallint) - e.g., 2013, 2014
- CalendarSemester (tinyint) - 1-2
- FiscalQuarter (tinyint) - 1-4
- FiscalYear (smallint)
- FiscalSemester (tinyint) - 1-2

**Date Ranges:** Covers years 2010-2014

### DimSalesTerritory (11 rows)
Sales territory geographical information.

**Primary Key:** SalesTerritoryKey (int)

**Important Columns:**
- SalesTerritoryAlternateKey (int)
- SalesTerritoryRegion (nvarchar(50)) - e.g., 'Northwest', 'Northeast'
- SalesTerritoryCountry (nvarchar(50)) - e.g., 'United States', 'Canada'
- SalesTerritoryGroup (nvarchar(50)) - e.g., 'North America', 'Europe'

### DimCurrency (105 rows)
Currency information for international sales.

**Primary Key:** CurrencyKey (int)

**Important Columns:**
- CurrencyAlternateKey (nchar(3)) - ISO code (e.g., 'USD', 'EUR', 'GBP')
- CurrencyName (nvarchar(50)) - e.g., 'US Dollar', 'Euro'

### DimPromotion (16 rows)
Promotion and discount campaign information.

**Primary Key:** PromotionKey (int)

**Important Columns:**
- PromotionAlternateKey (int)
- EnglishPromotionName (nvarchar(255))
- DiscountPct (float) - Discount percentage
- EnglishPromotionType (nvarchar(50))
- EnglishPromotionCategory (nvarchar(50))
- StartDate (datetime)
- EndDate (datetime)
- MinQty (int) - Minimum quantity required
- MaxQty (int) - Maximum quantity allowed

## Common Query Patterns

### Total Sales by Year
```sql
SELECT
    dt.CalendarYear,
    SUM(sal.SalesAmount) AS TotalSales
FROM FactInternetSales sal
INNER JOIN DimDate dt ON dt.DateKey = sal.OrderDateKey
GROUP BY dt.CalendarYear
ORDER BY dt.CalendarYear
```

### Top Customers
```sql
SELECT TOP 10
    cust.FirstName + ' ' + cust.LastName AS CustomerName,
    COUNT(DISTINCT sal.SalesOrderNumber) AS OrderCount,
    SUM(sal.SalesAmount) AS TotalPurchases
FROM FactInternetSales sal
INNER JOIN DimCustomer cust ON cust.CustomerKey = sal.CustomerKey
GROUP BY cust.CustomerKey, cust.FirstName, cust.LastName
ORDER BY TotalPurchases DESC
```

### Product Sales Analysis
```sql
SELECT
    prod.EnglishProductName,
    SUM(sal.OrderQuantity) AS UnitsSold,
    SUM(sal.SalesAmount) AS Revenue,
    AVG(sal.UnitPrice) AS AvgPrice
FROM FactInternetSales sal
INNER JOIN DimProduct prod ON prod.ProductKey = sal.ProductKey
GROUP BY prod.ProductKey, prod.EnglishProductName
ORDER BY Revenue DESC
```

### Sales by Territory
```sql
SELECT
    st.SalesTerritoryCountry,
    st.SalesTerritoryRegion,
    SUM(sal.SalesAmount) AS TotalSales,
    COUNT(DISTINCT sal.CustomerKey) AS UniqueCustomers
FROM FactInternetSales sal
INNER JOIN DimSalesTerritory st ON st.SalesTerritoryKey = sal.SalesTerritoryKey
GROUP BY st.SalesTerritoryCountry, st.SalesTerritoryRegion
ORDER BY TotalSales DESC
```

## Important Notes

1. **Date Keys**: Always join to DimDate using DateKey fields (OrderDateKey, DueDateKey, ShipDateKey)
2. **Customer Names**: Concatenate FirstName and LastName with space: `FirstName + ' ' + LastName`
3. **All Money Columns**: Use SUM() for aggregations, never COUNT()
4. **Year Queries**: Use DimDate.CalendarYear, not YEAR(OrderDate)
5. **TOP N Queries**: Use `TOP N` in SELECT, and always include ORDER BY
6. **NULL Promotions**: PromotionKey = 1 typically means "No Discount"
7. **Currency**: Most sales are in USD, but join to DimCurrency for currency name
8. **Fiscal vs Calendar**: Data supports both fiscal and calendar year analysis

## Schema Alias Conventions
- FactInternetSales: `sal`
- DimCustomer: `cust`
- DimProduct: `prod`
- DimDate: `dt`
- DimSalesTerritory: `st`
- DimCurrency: `curr`
- DimPromotion: `promo`
"""


def get_schema_context():
    """Return the schema context for RAG"""
    return SALES_SCHEMA_CONTEXT


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
