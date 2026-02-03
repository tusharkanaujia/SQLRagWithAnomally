-- ============================================
-- Daily Statistics Calculation
-- Run this as a scheduled job (after daily data load)
-- ============================================

DECLARE @BusinessDate DATE = CAST(GETDATE() AS DATE); -- Or pass as parameter

-- Clear existing stats for the date
DELETE FROM LBSAnomalyMetadata WHERE BusinessDate = @BusinessDate;

-- Calculate statistics by LBSCategory
INSERT INTO LBSAnomalyMetadata (
    BusinessDate, DimensionName, DimensionValue, MetricName,
    RecordCount, SumValue, MeanValue, StdDevValue, MinValue, MaxValue,
    P25Value, P50Value, P75Value, P95Value, P99Value
)
SELECT 
    BusinessDate,
    'LBSCategory' as DimensionName,
    LBSCategory as DimensionValue,
    'GBPIFRSBalanceSheetAmount' as MetricName,
    COUNT(*) as RecordCount,
    SUM(GBPIFRSBalanceSheetAmount) as SumValue,
    AVG(GBPIFRSBalanceSheetAmount) as MeanValue,
    STDEV(GBPIFRSBalanceSheetAmount) as StdDevValue,
    MIN(GBPIFRSBalanceSheetAmount) as MinValue,
    MAX(GBPIFRSBalanceSheetAmount) as MaxValue,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, LBSCategory) as P25Value,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, LBSCategory) as P50Value,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, LBSCategory) as P75Value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, LBSCategory) as P95Value,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, LBSCategory) as P99Value
FROM YourLBSFactTable
WHERE BusinessDate = @BusinessDate
GROUP BY BusinessDate, LBSCategory;

-- Calculate by Asset/Liability
INSERT INTO LBSAnomalyMetadata (
    BusinessDate, DimensionName, DimensionValue, MetricName,
    RecordCount, SumValue, MeanValue, StdDevValue, MinValue, MaxValue,
    P25Value, P50Value, P75Value, P95Value, P99Value
)
SELECT 
    BusinessDate,
    'AssetLiability' as DimensionName,
    AssetLiability as DimensionValue,
    'GBPIFRSBalanceSheetAmount' as MetricName,
    COUNT(*),
    SUM(GBPIFRSBalanceSheetAmount),
    AVG(GBPIFRSBalanceSheetAmount),
    STDEV(GBPIFRSBalanceSheetAmount),
    MIN(GBPIFRSBalanceSheetAmount),
    MAX(GBPIFRSBalanceSheetAmount),
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, AssetLiability),
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, AssetLiability),
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, AssetLiability),
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, AssetLiability),
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY GBPIFRSBalanceSheetAmount) OVER (PARTITION BY BusinessDate, AssetLiability)
FROM YourLBSFactTable
WHERE BusinessDate = @BusinessDate
GROUP BY BusinessDate, AssetLiability;

-- Add more dimensions as needed (LegalEntity, HqlaType, etc.)

PRINT 'Daily statistics calculated for ' + CAST(@BusinessDate AS VARCHAR(10));
GO
