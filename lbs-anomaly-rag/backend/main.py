"""FastAPI Application for Sales RAG System"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from services.sales_rag import SalesRAGService
from services.schema_context import get_example_queries
from services.anomaly_detection import SalesAnomalyDetector

app = FastAPI(
    title="Sales RAG API",
    description="Natural Language to SQL Query System for AdventureWorksDW2019",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rag_service = SalesRAGService()
anomaly_detector = SalesAnomalyDetector()


# Request/Response Models
class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question about sales data")
    execute: bool = Field(True, description="Whether to execute the generated SQL")
    limit: int = Field(100, description="Maximum number of rows to return", ge=1, le=10000)


class SQLValidateRequest(BaseModel):
    sql: str = Field(..., description="SQL query to validate")


class QueryResponse(BaseModel):
    question: str
    sql: str
    intent: str
    explanation: str
    data: List[Dict[str, Any]] = []
    row_count: int = 0
    columns: List[str] = []
    success: bool = True
    error: Optional[str] = None
    chart_suggestion: Optional[Dict[str, Any]] = None


class ExampleQuery(BaseModel):
    question: str
    sql: str
    intent: str


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sales RAG API",
        "version": "1.0.0",
        "endpoints": {
            "/query": "POST - Natural language query",
            "/examples": "GET - Example queries",
            "/validate": "POST - Validate SQL query",
            "/health": "GET - Health check"
        }
    }


@app.post("/query", response_model=QueryResponse)
async def query_sales_data(request: QueryRequest):
    """
    Convert natural language question to SQL and optionally execute it

    Example questions:
    - "What were the total sales in 2013?"
    - "Who are the top 10 customers?"
    - "Show sales by country"
    - "What products sold the most in quantity?"
    """
    try:
        result = rag_service.query(
            question=request.question,
            execute=request.execute,
            limit=request.limit
        )

        # Add chart suggestion if data is available
        if result.get("success") and result.get("data"):
            chart = rag_service.get_chart_suggestion(
                intent=result["intent"],
                columns=result["columns"],
                data=result["data"]
            )
            result["chart_suggestion"] = chart

        return QueryResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-sql")
async def generate_sql_only(question: str = Query(..., description="Natural language question")):
    """
    Generate SQL query without executing it

    This endpoint only generates the SQL query from natural language
    without executing it against the database.
    """
    try:
        result = rag_service.generate_sql(question)
        return {
            "question": question,
            "sql": result["sql"],
            "intent": result["intent"],
            "explanation": result["explanation"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute-sql")
async def execute_sql(
    sql: str = Query(..., description="SQL query to execute"),
    limit: int = Query(100, description="Maximum rows to return", ge=1, le=10000)
):
    """
    Execute a SQL query directly

    This endpoint allows you to execute a SQL query without going through
    the natural language generation step.
    """
    try:
        result = rag_service.execute_query(sql, limit)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Query execution failed"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate")
async def validate_sql(request: SQLValidateRequest):
    """
    Validate SQL query syntax without executing it

    This endpoint checks if the SQL query is syntactically correct
    without actually running it.
    """
    try:
        result = rag_service.validate_sql(request.sql)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/examples", response_model=List[ExampleQuery])
async def get_examples():
    """
    Get example natural language questions and their SQL queries

    These examples demonstrate the types of questions you can ask
    and the corresponding SQL queries that will be generated.
    """
    return get_example_queries()


@app.get("/schema")
async def get_schema_info():
    """
    Get database schema information

    Returns information about the tables, columns, and relationships
    in the AdventureWorksDW2019 database.
    """
    from services.schema_context import get_schema_context

    return {
        "database": "AdventureWorksDW2019",
        "schema_context": get_schema_context(),
        "tables": {
            "fact": ["FactInternetSales"],
            "dimensions": [
                "DimCustomer",
                "DimProduct",
                "DimDate",
                "DimSalesTerritory",
                "DimCurrency",
                "DimPromotion"
            ]
        }
    }


@app.get("/anomalies/all")
async def detect_all_anomalies():
    """
    Detect all types of anomalies in sales data

    Runs comprehensive anomaly detection including:
    - Time series anomalies (daily and monthly)
    - Statistical anomalies (products and customers)
    - Comparative anomalies (YoY and MoM)
    """
    try:
        result = anomaly_detector.detect_all_anomalies()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies/time-series")
async def detect_time_series(
    metric: str = Query("SalesAmount", description="Metric to analyze"),
    granularity: str = Query("daily", description="Time granularity: daily, weekly, monthly"),
    lookback_days: int = Query(90, description="Number of days to analyze", ge=7, le=365)
):
    """
    Detect time series anomalies in sales data

    Identifies unusual spikes or drops in sales over time using
    moving averages and standard deviation.
    """
    try:
        result = anomaly_detector.detect_time_series_anomalies(
            metric=metric,
            granularity=granularity,
            lookback_days=lookback_days
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies/statistical")
async def detect_statistical(
    dimension: str = Query("ProductKey", description="Dimension to analyze"),
    metric: str = Query("SalesAmount", description="Metric to analyze"),
    method: str = Query("zscore", description="Detection method: zscore, iqr, isolation_forest")
):
    """
    Detect statistical anomalies using Z-score, IQR, or Isolation Forest

    Identifies outliers in product sales, customer purchases, etc.
    """
    try:
        result = anomaly_detector.detect_statistical_anomalies(
            dimension=dimension,
            metric=metric,
            method=method
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies/comparative")
async def detect_comparative(
    comparison_type: str = Query("yoy", description="Comparison type: yoy, mom, qoq"),
    metric: str = Query("SalesAmount", description="Metric to compare"),
    threshold_pct: float = Query(20.0, description="Percentage threshold for anomaly", ge=1.0, le=100.0)
):
    """
    Detect anomalies by comparing current to previous period

    Compares:
    - YoY: Year-over-Year
    - MoM: Month-over-Month
    - QoQ: Quarter-over-Quarter
    """
    try:
        result = anomaly_detector.detect_comparative_anomalies(
            comparison_type=comparison_type,
            metric=metric,
            threshold_pct=threshold_pct
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-endpoint")
async def test_endpoint():
    """Test endpoint to verify registration"""
    return {"message": "test endpoint works!"}


@app.get("/anomalies/day-on-day")
async def detect_day_on_day(
    dimension: str = Query("ProductKey", description="Dimension: ProductKey, CustomerKey, TerritoryKey, PromotionKey"),
    metric: str = Query("SalesAmount", description="Metric to analyze: SalesAmount, OrderQuantity"),
    threshold_pct: float = Query(20.0, description="Percentage threshold for anomaly", ge=1.0, le=100.0),
    lookback_days: int = Query(30, description="Number of days to analyze", ge=7, le=90),
    top_n: int = Query(50, description="Top N dimension values to analyze", ge=10, le=200)
):
    """
    Detect day-on-day anomalies for a specific dimension

    Compares each day's performance to the previous day for specific:
    - Products
    - Customers
    - Territories
    - Promotions

    Identifies sudden spikes or drops in sales for each dimension value.
    """
    try:
        result = anomaly_detector.detect_day_on_day_anomalies(
            dimension=dimension,
            metric=metric,
            threshold_pct=threshold_pct,
            lookback_days=lookback_days,
            top_n=top_n
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint

    Verifies that the API and its dependencies (database, LLM) are working.
    """
    health_status = {
        "api": "healthy",
        "database": "unknown",
        "llm": "unknown"
    }

    # Check database
    try:
        result = rag_service.execute_query("SELECT TOP 1 1 AS test FROM FactInternetSales", limit=1)
        health_status["database"] = "healthy" if result["success"] else "unhealthy"
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)[:100]}"

    # Check LLM
    try:
        test_result = rag_service._call_llama("Test", "Respond with 'OK'")
        health_status["llm"] = "healthy" if test_result else "unhealthy"
    except Exception as e:
        health_status["llm"] = f"unhealthy: {str(e)[:100]}"

    # Overall status
    all_healthy = all(
        status == "healthy"
        for key, status in health_status.items()
        if key != "api"
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "components": health_status
    }


if __name__ == "__main__":
    import uvicorn
    from config.settings import settings

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=True
    )
