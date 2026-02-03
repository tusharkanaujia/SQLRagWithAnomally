"""Application configuration settings"""
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
