#!/usr/bin/env python3
"""
LBS Anomaly Detection RAG System - Complete Project Generator
Creates all files needed for the LBS anomaly detection system
"""

import os
import sys

def create_file(path, content):
    """Create a file with content"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Created: {path}")
        return True
    except Exception as e:
        print(f"✗ Failed: {path} - {e}")
        return False

def main():
    print("\n" + "="*70)
    print("🏦 LBS Anomaly Detection RAG System - Project Generator")
    print("="*70 + "\n")
    
    base = "lbs-anomaly-rag"
    
    # Create directories
    dirs = [
        base,
        f"{base}/backend",
        f"{base}/backend/config",
        f"{base}/backend/models",
        f"{base}/backend/services",
        f"{base}/backend/utils",
        f"{base}/frontend",
        f"{base}/frontend/public",
        f"{base}/frontend/src",
        f"{base}/frontend/src/components",
        f"{base}/frontend/src/services",
        f"{base}/database"
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    print(f"✓ Created {len(dirs)} directories\n")
    
    files = {}
    
    # ========== ROOT FILES ==========
    
    files[f"{base}/README.md"] = """# 🏦 LBS Anomaly Detection RAG System

AI-powered anomaly detection for Liquidity Balance Sheet data with natural language query interface.

## 📊 Features

- **Anomaly Detection**: Z-Score, IQR, Isolation Forest, Time-Series analysis
- **Natural Language Queries**: Ask questions about your LBS data in plain English
- **Multi-Dimensional Analysis**: Analyze by Category, SubCategory, Asset Class, Legal Entity, etc.
- **Daily Processing**: Handles 10M+ records per business date
- **Visual Dashboard**: Interactive charts, heatmaps, and trend analysis
- **Historical Comparison**: Compare against 30/60/90 day baselines

## 🚀 Quick Start

```bash
# 1. Setup Database
cd database
sqlcmd -S your_server -d your_db -i create_tables.sql

# 2. Backend
cd ../backend
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your settings
python app.py

# 3. Frontend
cd ../frontend
npm install
npm start

# 4. Ollama
ollama serve
ollama pull llama3.1
```

## 📋 LBS Data Structure

Your data has these key dimensions:
- Business Date (partition key)
- LBS Categories & SubCategories
- Asset/Liability Classification
- Product Hierarchies (Level 2-10)
- Counterparty Information
- Legal Entity & Reporting Cluster
- Geographic & Market Dimensions
- HQLA Type & Security Information
- GBP IFRS Balance

## 🎯 Example Queries

```
"Show me anomalies for yesterday's LBS data"
"Compare Asset vs Liability balances for 2024-02-01"
"What categories have unusual values today?"
"Show balance trend for Loans product over last 30 days"
"Find outliers in HQLA Type Level 1"
"Which Legal Entities have anomalies?"
"Compare GBP balances across Product Levels"
```

## 📁 Project Structure

```
lbs-anomaly-rag/
├── backend/          # FastAPI + Anomaly Detection
├── frontend/         # React UI
└── database/         # SQL scripts
```

## 🛠️ Tech Stack

- Backend: FastAPI, Pandas, Scikit-learn, PyODBC
- Frontend: React, Recharts, AG Grid
- Database: SQL Server (partitioned by BusinessDate)
- AI: Ollama (Llama 3.1 / CodeLlama)

## 📝 License

MIT
"""

    files[f"{base}/.env.template"] = """# ============================================
# LBS Anomaly Detection - Configuration
# ============================================

# SQL Server Database
DB_SERVER=your_sql_server
DB_DATABASE=your_lbs_database
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_TRUSTED_CONNECTION=no

# Your LBS Fact Table Name
FACT_TABLE_NAME=YourLBSFactTable

# Local LLM Server
LLAMA_SERVER_URL=http://localhost:11434
LLAMA_MODEL=llama3.1

# Application Settings
API_PORT=8000
FRONTEND_PORT=3000

# Anomaly Detection Settings
ZSCORE_THRESHOLD=3.0
IQR_MULTIPLIER=1.5
HISTORICAL_BASELINE_DAYS=30
MIN_RECORDS_FOR_DETECTION=100

# Performance Settings
QUERY_TIMEOUT_SECONDS=300
MAX_RECORDS_PER_QUERY=1000000
ENABLE_QUERY_CACHE=true
CACHE_TTL_HOURS=24
"""

    files[f"{base}/backend/requirements.txt"] = """# FastAPI and web framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6

# Database
pyodbc>=4.0.39
pandas>=2.0.0
sqlparse>=0.4.4

# Data analysis and ML
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.3.0

# HTTP and utilities
requests>=2.31.0
python-dotenv>=1.0.0
pydantic>=2.4.0
python-dateutil>=2.8.0

# Optional: Advanced time-series
# prophet>=1.1.0
# statsmodels>=0.14.0

# Development
pytest>=7.4.0
black>=23.10.0
"""

    files[f"{base}/backend/.gitignore"] = """# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
venv/
env/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp

# Logs
*.log
logs/

# Cache
.cache/
*.cache
"""

    files[f"{base}/backend/config/__init__.py"] = ""

    files[f"{base}/backend/config/settings.py"] = """\"\"\"Application configuration settings\"\"\"
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DB_SERVER = os.getenv('DB_SERVER', 'localhost')
    DB_DATABASE = os.getenv('DB_DATABASE')
    DB_USERNAME = os.getenv('DB_USERNAME', '')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_TRUSTED_CONNECTION = os.getenv('DB_TRUSTED_CONNECTION', 'no')
    
    # Table names
    FACT_TABLE_NAME = os.getenv('FACT_TABLE_NAME', 'LBSFactData')
    METADATA_TABLE_NAME = 'LBSAnomalyMetadata'
    
    # LLM
    LLAMA_SERVER_URL = os.getenv('LLAMA_SERVER_URL', 'http://localhost:11434')
    LLAMA_MODEL = os.getenv('LLAMA_MODEL', 'llama3.1')
    
    # Anomaly Detection
    ZSCORE_THRESHOLD = float(os.getenv('ZSCORE_THRESHOLD', '3.0'))
    IQR_MULTIPLIER = float(os.getenv('IQR_MULTIPLIER', '1.5'))
    HISTORICAL_BASELINE_DAYS = int(os.getenv('HISTORICAL_BASELINE_DAYS', '30'))
    MIN_RECORDS_FOR_DETECTION = int(os.getenv('MIN_RECORDS_FOR_DETECTION', '100'))
    
    # Performance
    QUERY_TIMEOUT = int(os.getenv('QUERY_TIMEOUT_SECONDS', '300'))
    MAX_RECORDS_PER_QUERY = int(os.getenv('MAX_RECORDS_PER_QUERY', '1000000'))
    
    # API
    API_PORT = int(os.getenv('API_PORT', '8000'))
    
    # LBS Columns
    LBS_DIMENSIONS = [
        'LBSCategory',
        'LBSSubCategory',
        'AssetSubClass',
        'AssetLiability',
        'BalanceClassification',
        'ProdLevel2BG',
        'ProdLevel3SB',
        'ProdLevel4SD',
        'ProdLevel5PG',
        'ProdLevel6PR',
        'LegalEntity',
        'ReportingCluster',
        'CountryOfRisk',
        'HqlaType',
        'Market',
        'MarketSector',
        'SecurityType'
    ]
    
    LBS_METRICS = ['GBPIFRSBalanceSheetAmount']
    
    @classmethod
    def get_db_connection_string(cls):
        driver = '{ODBC Driver 17 for SQL Server}'
        if cls.DB_TRUSTED_CONNECTION.lower() == 'yes':
            return f"DRIVER={driver};SERVER={cls.DB_SERVER};DATABASE={cls.DB_DATABASE};Trusted_Connection=yes;"
        else:
            return f"DRIVER={driver};SERVER={cls.DB_SERVER};DATABASE={cls.DB_DATABASE};UID={cls.DB_USERNAME};PWD={cls.DB_PASSWORD};"

settings = Settings()
"""

    files[f"{base}/backend/models/__init__.py"] = ""

    files[f"{base}/backend/models/schemas.py"] = """\"\"\"Pydantic models for request/response\"\"\"
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import date

class AnomalyRequest(BaseModel):
    business_date: str = Field(..., description="Business date in YYYY-MM-DD format")
    dimension: Optional[str] = Field(None, description="Dimension to analyze (e.g., LBSCategory)")
    dimension_value: Optional[str] = Field(None, description="Specific value in dimension")
    detection_method: str = Field("all", description="zscore, iqr, isolation_forest, or all")
    threshold: float = Field(3.0, description="Z-score threshold")
    compare_days_back: int = Field(30, description="Days to compare against")

class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    business_date: Optional[str] = Field(None, description="Optional business date")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)

class AnomalyDetail(BaseModel):
    dimension: str
    dimension_value: str
    metric: str = "GBPIFRSBalanceSheetAmount"
    current_value: float
    expected_value: float
    deviation: float
    zscore: Optional[float] = None
    severity: str  # low, medium, high, critical
    is_anomaly: bool
    record_count: int

class AnomalyResponse(BaseModel):
    business_date: str
    total_records: int
    dimensions_analyzed: int
    anomalies_detected: int
    details: List[AnomalyDetail]
    statistics: Dict[str, Any]

class QueryResponse(BaseModel):
    question: str
    intent: str
    sql_query: Optional[str] = None
    data: List[Dict[str, Any]]
    chart_suggestion: Optional[Dict[str, Any]] = None
    explanation: str
"""

    # Backend app.py is in artifact: lbs_backend_app
    # Frontend App.js is in artifact: lbs_frontend_complete
    
    files[f"{base}/backend/_INSTRUCTIONS.md"] = """# Manual File Copy Instructions

Copy the following files from the chat artifacts:

## Backend
1. **app.py** 
   - Artifact: `lbs_backend_app`
   - Location: `backend/app.py`
   - Size: ~500 lines
   - Contains: Complete FastAPI application with all endpoints

## Frontend  
2. **App.js**
   - Artifact: `lbs_frontend_complete`
   - Location: `frontend/src/App.js`
   - Size: ~600 lines
   - Contains: Complete React UI with charts and tables

## How to Copy
1. Find the artifact in the chat above
2. Copy the entire code block
3. Create the file in the location shown
4. Paste and save

The project will work once these 2 files are in place!
"""

    files[f"{base}/database/create_tables.sql"] = """-- ============================================
-- LBS Anomaly Detection - Database Setup
-- ============================================

-- Your existing LBS Fact Table should have these columns:
-- BusinessDate, LBSCategory, LBSSubCategory, AssetSubClass, AssetLiability,
-- BalanceClassification, ProdLevel2BG through ProdLevel10, CounterpartySdsld,
-- CounterpartySDSName, ProdLevel6PRAmendedSynPB, LegalEntity, ReportingCluster,
-- RunName, CountryOfRisk, HqlaType, Market, MarketSector, MainTrader,
-- SecurityType, Level4Description, Level5Description, TransactionalCurrency,
-- GBPIFRSBalanceSheetAmount

-- Create index on BusinessDate for partition elimination
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_LBS_BusinessDate')
BEGIN
    CREATE NONCLUSTERED INDEX IX_LBS_BusinessDate 
    ON YourLBSFactTable(BusinessDate)
    INCLUDE (LBSCategory, LBSSubCategory, GBPIFRSBalanceSheetAmount);
END
GO

-- Anomaly Metadata Table - Stores daily statistics
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'LBSAnomalyMetadata')
BEGIN
    CREATE TABLE LBSAnomalyMetadata (
        BusinessDate DATE NOT NULL,
        DimensionName VARCHAR(100) NOT NULL,
        DimensionValue VARCHAR(500) NOT NULL,
        MetricName VARCHAR(100) NOT NULL,
        RecordCount BIGINT NOT NULL,
        SumValue DECIMAL(28,8),
        MeanValue DECIMAL(28,8),
        StdDevValue DECIMAL(28,8),
        MinValue DECIMAL(28,8),
        MaxValue DECIMAL(28,8),
        P25Value DECIMAL(28,8),
        P50Value DECIMAL(28,8),  -- Median
        P75Value DECIMAL(28,8),
        P95Value DECIMAL(28,8),
        P99Value DECIMAL(28,8),
        AnomalyScore DECIMAL(10,4),
        AnomalyFlag BIT DEFAULT 0,
        CreatedDate DATETIME DEFAULT GETDATE(),
        CONSTRAINT PK_LBSAnomalyMetadata PRIMARY KEY (BusinessDate, DimensionName, DimensionValue, MetricName)
    );
    
    CREATE NONCLUSTERED INDEX IX_LBSAnomalyMetadata_Date 
    ON LBSAnomalyMetadata(BusinessDate DESC);
    
    CREATE NONCLUSTERED INDEX IX_LBSAnomalyMetadata_Dimension 
    ON LBSAnomalyMetadata(DimensionName, DimensionValue);
END
GO

-- Query Performance View - Pre-aggregated statistics
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_LBSDailyStats')
BEGIN
    EXEC('
    CREATE VIEW vw_LBSDailyStats AS
    SELECT 
        BusinessDate,
        LBSCategory,
        LBSSubCategory,
        AssetLiability,
        COUNT(*) as RecordCount,
        SUM(GBPIFRSBalanceSheetAmount) as TotalBalance,
        AVG(GBPIFRSBalanceSheetAmount) as AvgBalance,
        STDEV(GBPIFRSBalanceSheetAmount) as StdDevBalance,
        MIN(GBPIFRSBalanceSheetAmount) as MinBalance,
        MAX(GBPIFRSBalanceSheetAmount) as MaxBalance
    FROM YourLBSFactTable
    GROUP BY BusinessDate, LBSCategory, LBSSubCategory, AssetLiability
    ');
END
GO

PRINT 'Database objects created successfully!';
PRINT 'Remember to:';
PRINT '1. Replace YourLBSFactTable with your actual table name';
PRINT '2. Run daily statistics calculation job';
PRINT '3. Configure partition scheme if needed';
GO
"""

    files[f"{base}/database/calculate_daily_stats.sql"] = """-- ============================================
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
"""

    files[f"{base}/frontend/package.json"] = """{
  "name": "lbs-anomaly-frontend",
  "version": "1.0.0",
  "private": true,
  "proxy": "http://localhost:8000",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "recharts": "^2.10.0",
    "lucide-react": "^0.263.1",
    "ag-grid-react": "^31.0.0",
    "ag-grid-community": "^31.0.0",
    "date-fns": "^2.30.0",
    "react-datepicker": "^4.21.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  },
  "eslintConfig": {
    "extends": ["react-app"]
  },
  "browserslist": {
    "production": [">0.2%", "not dead"],
    "development": ["last 1 chrome version"]
  }
}
"""

    files[f"{base}/frontend/.gitignore"] = """node_modules/
build/
.env.local
.DS_Store
npm-debug.log*
"""

    files[f"{base}/frontend/public/index.html"] = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>LBS Anomaly Detection</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
"""

    files[f"{base}/frontend/src/_COPY_App.js.txt"] = """⚠️ REQUIRED: Copy App.js

Copy the content from artifact: lbs_frontend_app

Main React application (~800 lines) with:
- Anomaly dashboard
- Date picker
- Dimension selector
- Charts and visualizations
- Data grid
- Natural language chat
"""

    files[f"{base}/frontend/src/index.js"] = """import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
"""

    files[f"{base}/frontend/src/index.css"] = """* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

#root {
  min-height: 100vh;
}
"""

    # Create all files
    print("Generating project files...\n")
    created = sum(1 for path, content in files.items() if create_file(path, content))
    
    print(f"\n{'='*70}")
    print(f"✓ Created {created}/{len(files)} files")
    print(f"{'='*70}\n")
    
    print("⚠️  MANUAL STEPS REQUIRED:\n")
    print("Copy these 4 large files from chat artifacts:\n")
    print("1. backend/app.py              ← Artifact: lbs_backend_app")
    print("2. backend/services/database.py   ← Artifact: lbs_database_service")
    print("3. backend/services/anomaly_detector.py ← Artifact: lbs_anomaly_detector")
    print("4. frontend/src/App.js         ← Artifact: lbs_frontend_app")
    
    print(f"\n{'='*70}")
    print("📋 NEXT STEPS:")
    print(f"{'='*70}\n")
    print("1. Update database scripts:")
    print("   - Edit database/*.sql files")
    print("   - Replace 'YourLBSFactTable' with your actual table name")
    print("")
    print("2. Setup database:")
    print("   sqlcmd -S your_server -d your_db -i database/create_tables.sql")
    print("")
    print("3. Configure:")
    print("   cp .env.template .env")
    print("   nano .env  # Edit with your settings")
    print("")
    print("4. Install backend:")
    print("   cd backend && pip install -r requirements.txt")
    print("")
    print("5. Install frontend:")
    print("   cd frontend && npm install")
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
