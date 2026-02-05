"""Pydantic models for request/response schemas"""
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
