-- ============================================
-- Internet Sales Data Warehouse - Database Setup
-- Star Schema for Sales Analytics
-- ============================================

USE [YourDatabaseName];
GO

-- ============================================
-- Dimension Tables
-- ============================================

-- DimCustomer: Customer demographic information
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DimCustomer')
BEGIN
    CREATE TABLE dbo.DimCustomer (
        CustomerKey INT PRIMARY KEY IDENTITY(1,1),
        CustomerAlternateKey NVARCHAR(15) NOT NULL,
        Title NVARCHAR(8) NULL,
        FirstName NVARCHAR(50) NULL,
        MiddleName NVARCHAR(50) NULL,
        LastName NVARCHAR(50) NULL,
        NameStyle BIT NULL,
        BirthDate DATE NULL,
        MaritalStatus NCHAR(1) NULL,
        Suffix NVARCHAR(10) NULL,
        Gender NVARCHAR(1) NULL,
        EmailAddress NVARCHAR(50) NULL,
        YearlyIncome MONEY NULL,
        TotalChildren TINYINT NULL,
        NumberChildrenAtHome TINYINT NULL,
        EnglishEducation NVARCHAR(40) NULL,
        SpanishEducation NVARCHAR(40) NULL,
        FrenchEducation NVARCHAR(40) NULL,
        EnglishOccupation NVARCHAR(100) NULL,
        SpanishOccupation NVARCHAR(100) NULL,
        FrenchOccupation NVARCHAR(100) NULL,
        HouseOwnerFlag NCHAR(1) NULL,
        NumberCarsOwned TINYINT NULL,
        AddressLine1 NVARCHAR(120) NULL,
        AddressLine2 NVARCHAR(120) NULL,
        Phone NVARCHAR(20) NULL,
        DateFirstPurchase DATE NULL,
        CommuteDistance NVARCHAR(15) NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        ModifiedDate DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_DimCustomer_AlternateKey ON dbo.DimCustomer(CustomerAlternateKey);
    CREATE INDEX IX_DimCustomer_Name ON dbo.DimCustomer(LastName, FirstName);
    PRINT 'Table DimCustomer created successfully';
END
GO

-- DimProduct: Product information
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DimProduct')
BEGIN
    CREATE TABLE dbo.DimProduct (
        ProductKey INT PRIMARY KEY IDENTITY(1,1),
        ProductAlternateKey NVARCHAR(25) NOT NULL,
        ProductSubcategoryKey INT NULL,
        WeightUnitMeasureCode NCHAR(3) NULL,
        SizeUnitMeasureCode NCHAR(3) NULL,
        EnglishProductName NVARCHAR(50) NOT NULL,
        SpanishProductName NVARCHAR(50) NULL,
        FrenchProductName NVARCHAR(50) NULL,
        StandardCost MONEY NULL,
        FinishedGoodsFlag BIT NOT NULL,
        Color NVARCHAR(15) NULL,
        SafetyStockLevel SMALLINT NULL,
        ReorderPoint SMALLINT NULL,
        ListPrice MONEY NULL,
        Size NVARCHAR(50) NULL,
        SizeRange NVARCHAR(50) NULL,
        Weight FLOAT NULL,
        DaysToManufacture INT NULL,
        ProductLine NCHAR(2) NULL,
        DealerPrice MONEY NULL,
        Class NCHAR(2) NULL,
        Style NCHAR(2) NULL,
        ModelName NVARCHAR(50) NULL,
        LargePhoto VARBINARY(MAX) NULL,
        EnglishDescription NVARCHAR(400) NULL,
        FrenchDescription NVARCHAR(400) NULL,
        ChineseDescription NVARCHAR(400) NULL,
        ArabicDescription NVARCHAR(400) NULL,
        HebrewDescription NVARCHAR(400) NULL,
        ThaiDescription NVARCHAR(400) NULL,
        GermanDescription NVARCHAR(400) NULL,
        JapaneseDescription NVARCHAR(400) NULL,
        TurkishDescription NVARCHAR(400) NULL,
        StartDate DATETIME NULL,
        EndDate DATETIME NULL,
        Status NVARCHAR(7) NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        ModifiedDate DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_DimProduct_AlternateKey ON dbo.DimProduct(ProductAlternateKey);
    CREATE INDEX IX_DimProduct_Name ON dbo.DimProduct(EnglishProductName);
    PRINT 'Table DimProduct created successfully';
END
GO

-- DimDate: Date dimension for time-based analysis
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DimDate')
BEGIN
    CREATE TABLE dbo.DimDate (
        DateKey INT PRIMARY KEY,
        FullDateAlternateKey DATE NOT NULL,
        DayNumberOfWeek TINYINT NOT NULL,
        EnglishDayNameOfWeek NVARCHAR(10) NOT NULL,
        SpanishDayNameOfWeek NVARCHAR(10) NULL,
        FrenchDayNameOfWeek NVARCHAR(10) NULL,
        DayNumberOfMonth TINYINT NOT NULL,
        DayNumberOfYear SMALLINT NOT NULL,
        WeekNumberOfYear TINYINT NOT NULL,
        EnglishMonthName NVARCHAR(10) NOT NULL,
        SpanishMonthName NVARCHAR(10) NULL,
        FrenchMonthName NVARCHAR(10) NULL,
        MonthNumberOfYear TINYINT NOT NULL,
        CalendarQuarter TINYINT NOT NULL,
        CalendarYear SMALLINT NOT NULL,
        CalendarSemester TINYINT NOT NULL,
        FiscalQuarter TINYINT NOT NULL,
        FiscalYear SMALLINT NOT NULL,
        FiscalSemester TINYINT NOT NULL,
        CreatedDate DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_DimDate_FullDate ON dbo.DimDate(FullDateAlternateKey);
    CREATE INDEX IX_DimDate_Year ON dbo.DimDate(CalendarYear, CalendarQuarter);
    PRINT 'Table DimDate created successfully';
END
GO

-- DimSalesTerritory: Sales territory information
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DimSalesTerritory')
BEGIN
    CREATE TABLE dbo.DimSalesTerritory (
        SalesTerritoryKey INT PRIMARY KEY IDENTITY(1,1),
        SalesTerritoryAlternateKey INT NULL,
        SalesTerritoryRegion NVARCHAR(50) NOT NULL,
        SalesTerritoryCountry NVARCHAR(50) NOT NULL,
        SalesTerritoryGroup NVARCHAR(50) NULL,
        SalesTerritoryImage VARBINARY(MAX) NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        ModifiedDate DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_DimSalesTerritory_Region ON dbo.DimSalesTerritory(SalesTerritoryRegion);
    CREATE INDEX IX_DimSalesTerritory_Country ON dbo.DimSalesTerritory(SalesTerritoryCountry);
    PRINT 'Table DimSalesTerritory created successfully';
END
GO

-- DimCurrency: Currency information for international sales
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DimCurrency')
BEGIN
    CREATE TABLE dbo.DimCurrency (
        CurrencyKey INT PRIMARY KEY IDENTITY(1,1),
        CurrencyAlternateKey NCHAR(3) NOT NULL,
        CurrencyName NVARCHAR(50) NOT NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        ModifiedDate DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_DimCurrency_AlternateKey ON dbo.DimCurrency(CurrencyAlternateKey);
    PRINT 'Table DimCurrency created successfully';
END
GO

-- DimPromotion: Promotion and discount information
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DimPromotion')
BEGIN
    CREATE TABLE dbo.DimPromotion (
        PromotionKey INT PRIMARY KEY IDENTITY(1,1),
        PromotionAlternateKey INT NULL,
        EnglishPromotionName NVARCHAR(255) NULL,
        SpanishPromotionName NVARCHAR(255) NULL,
        FrenchPromotionName NVARCHAR(255) NULL,
        DiscountPct FLOAT NULL,
        EnglishPromotionType NVARCHAR(50) NULL,
        SpanishPromotionType NVARCHAR(50) NULL,
        FrenchPromotionType NVARCHAR(50) NULL,
        EnglishPromotionCategory NVARCHAR(50) NULL,
        SpanishPromotionCategory NVARCHAR(50) NULL,
        FrenchPromotionCategory NVARCHAR(50) NULL,
        StartDate DATETIME NOT NULL,
        EndDate DATETIME NULL,
        MinQty INT NULL,
        MaxQty INT NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        ModifiedDate DATETIME DEFAULT GETDATE()
    );

    CREATE INDEX IX_DimPromotion_Dates ON dbo.DimPromotion(StartDate, EndDate);
    PRINT 'Table DimPromotion created successfully';
END
GO

-- ============================================
-- Fact Table
-- ============================================

-- FactInternetSales: Internet sales transactions
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'FactInternetSales')
BEGIN
    CREATE TABLE dbo.FactInternetSales (
        ProductKey INT NOT NULL,
        OrderDateKey INT NOT NULL,
        DueDateKey INT NOT NULL,
        ShipDateKey INT NOT NULL,
        CustomerKey INT NOT NULL,
        PromotionKey INT NOT NULL,
        CurrencyKey INT NOT NULL,
        SalesTerritoryKey INT NOT NULL,
        SalesOrderNumber NVARCHAR(20) NOT NULL,
        SalesOrderLineNumber TINYINT NOT NULL,
        RevisionNumber TINYINT NOT NULL DEFAULT 0,
        OrderQuantity SMALLINT NOT NULL,
        UnitPrice MONEY NOT NULL,
        ExtendedAmount MONEY NOT NULL,
        UnitPriceDiscountPct FLOAT NOT NULL DEFAULT 0,
        DiscountAmount FLOAT NOT NULL DEFAULT 0,
        ProductStandardCost MONEY NOT NULL,
        TotalProductCost MONEY NOT NULL,
        SalesAmount MONEY NOT NULL,
        TaxAmt MONEY NOT NULL DEFAULT 0,
        Freight MONEY NOT NULL DEFAULT 0,
        CarrierTrackingNumber NVARCHAR(25) NULL,
        CustomerPONumber NVARCHAR(25) NULL,
        OrderDate DATETIME NULL,
        DueDate DATETIME NULL,
        ShipDate DATETIME NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        ModifiedDate DATETIME DEFAULT GETDATE(),

        -- Composite primary key
        CONSTRAINT PK_FactInternetSales PRIMARY KEY CLUSTERED (SalesOrderNumber, SalesOrderLineNumber),

        -- Foreign keys
        CONSTRAINT FK_FactInternetSales_DimProduct FOREIGN KEY (ProductKey)
            REFERENCES dbo.DimProduct(ProductKey),
        CONSTRAINT FK_FactInternetSales_DimCustomer FOREIGN KEY (CustomerKey)
            REFERENCES dbo.DimCustomer(CustomerKey),
        CONSTRAINT FK_FactInternetSales_DimOrderDate FOREIGN KEY (OrderDateKey)
            REFERENCES dbo.DimDate(DateKey),
        CONSTRAINT FK_FactInternetSales_DimDueDate FOREIGN KEY (DueDateKey)
            REFERENCES dbo.DimDate(DateKey),
        CONSTRAINT FK_FactInternetSales_DimShipDate FOREIGN KEY (ShipDateKey)
            REFERENCES dbo.DimDate(DateKey),
        CONSTRAINT FK_FactInternetSales_DimSalesTerritory FOREIGN KEY (SalesTerritoryKey)
            REFERENCES dbo.DimSalesTerritory(SalesTerritoryKey),
        CONSTRAINT FK_FactInternetSales_DimCurrency FOREIGN KEY (CurrencyKey)
            REFERENCES dbo.DimCurrency(CurrencyKey),
        CONSTRAINT FK_FactInternetSales_DimPromotion FOREIGN KEY (PromotionKey)
            REFERENCES dbo.DimPromotion(PromotionKey)
    );

    -- Performance indexes
    CREATE INDEX IX_FactInternetSales_OrderDate ON dbo.FactInternetSales(OrderDateKey)
        INCLUDE (SalesAmount, OrderQuantity);
    CREATE INDEX IX_FactInternetSales_Customer ON dbo.FactInternetSales(CustomerKey)
        INCLUDE (SalesAmount);
    CREATE INDEX IX_FactInternetSales_Product ON dbo.FactInternetSales(ProductKey)
        INCLUDE (SalesAmount, OrderQuantity);
    CREATE INDEX IX_FactInternetSales_Territory ON dbo.FactInternetSales(SalesTerritoryKey)
        INCLUDE (SalesAmount);

    PRINT 'Table FactInternetSales created successfully';
END
GO

-- ============================================
-- Views for Common Queries
-- ============================================

-- Sales with all dimension details (matches your original query)
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_InternetSalesComplete')
    DROP VIEW dbo.vw_InternetSalesComplete;
GO

CREATE VIEW dbo.vw_InternetSalesComplete AS
SELECT
    -- Fact measures
    sal.SalesOrderNumber,
    sal.SalesOrderLineNumber,
    sal.OrderQuantity,
    sal.UnitPrice,
    sal.SalesAmount,
    sal.TaxAmt,
    sal.Freight,
    sal.ExtendedAmount,
    sal.DiscountAmount,
    sal.TotalProductCost,

    -- Customer dimensions
    cust.CustomerKey,
    cust.CustomerAlternateKey,
    cust.FirstName,
    cust.LastName,
    cust.EmailAddress,
    cust.YearlyIncome,
    cust.EnglishEducation,
    cust.EnglishOccupation,
    cust.Gender,
    cust.MaritalStatus,
    cust.TotalChildren,
    cust.NumberChildrenAtHome,
    cust.HouseOwnerFlag,
    cust.NumberCarsOwned,
    cust.CommuteDistance,

    -- Product dimensions
    prod.ProductKey,
    prod.ProductAlternateKey,
    prod.EnglishProductName,
    prod.Color,
    prod.Size,
    prod.ProductLine,
    prod.ModelName,
    prod.StandardCost,
    prod.ListPrice,

    -- Date dimensions
    dt.DateKey,
    dt.FullDateAlternateKey AS OrderDate,
    dt.EnglishDayNameOfWeek,
    dt.EnglishMonthName,
    dt.CalendarQuarter,
    dt.CalendarYear,
    dt.FiscalQuarter,
    dt.FiscalYear,

    -- Sales Territory dimensions
    st.SalesTerritoryKey,
    st.SalesTerritoryRegion,
    st.SalesTerritoryCountry,
    st.SalesTerritoryGroup,

    -- Currency dimensions
    curr.CurrencyKey,
    curr.CurrencyAlternateKey,
    curr.CurrencyName,

    -- Promotion dimensions
    promo.PromotionKey,
    promo.EnglishPromotionName,
    promo.DiscountPct,
    promo.EnglishPromotionType,
    promo.EnglishPromotionCategory

FROM dbo.FactInternetSales sal
INNER JOIN dbo.DimCustomer cust ON cust.CustomerKey = sal.CustomerKey
INNER JOIN dbo.DimProduct prod ON prod.ProductKey = sal.ProductKey
INNER JOIN dbo.DimDate dt ON dt.DateKey = sal.OrderDateKey
INNER JOIN dbo.DimSalesTerritory st ON st.SalesTerritoryKey = sal.SalesTerritoryKey
INNER JOIN dbo.DimCurrency curr ON curr.CurrencyKey = sal.CurrencyKey
INNER JOIN dbo.DimPromotion promo ON promo.PromotionKey = sal.PromotionKey;
GO

PRINT '========================================';
PRINT 'Internet Sales Data Warehouse Setup Complete!';
PRINT '========================================';
PRINT 'Tables Created:';
PRINT '  - DimCustomer';
PRINT '  - DimProduct';
PRINT '  - DimDate';
PRINT '  - DimSalesTerritory';
PRINT '  - DimCurrency';
PRINT '  - DimPromotion';
PRINT '  - FactInternetSales';
PRINT '';
PRINT 'Views Created:';
PRINT '  - vw_InternetSalesComplete';
PRINT '';
PRINT 'Next Steps:';
PRINT '  1. Replace [YourDatabaseName] with your actual database name';
PRINT '  2. Populate DimDate with date range data';
PRINT '  3. Load dimension data from your source systems';
PRINT '  4. Load fact data into FactInternetSales';
PRINT '  5. Consider partitioning FactInternetSales by OrderDateKey';
PRINT '========================================';
GO
