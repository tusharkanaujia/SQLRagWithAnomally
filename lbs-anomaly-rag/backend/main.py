"""FastAPI Application for RAG System"""
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from services.rag_service import RAGService
from services.schema_context import get_example_queries
from services.anomaly_detection import AnomalyDetector

app = FastAPI(
    title="Data Warehouse RAG API",
    description="Natural Language to SQL Query System for Data Warehouse",
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

# GZip compression middleware (compress responses > 1KB)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Initialize services
rag_service = RAGService()
anomaly_detector = AnomalyDetector()


# Request/Response Models
class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question about data")
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
        "message": "Data Warehouse RAG API",
        "version": "1.0.0",
        "endpoints": {
            "/query": "POST - Natural language query",
            "/examples": "GET - Example queries",
            "/validate": "POST - Validate SQL query",
            "/health": "GET - Health check"
        }
    }


@app.post("/query", response_model=QueryResponse)
async def query_data(request: QueryRequest):
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
    in the data warehouse.
    """
    from services.schema_context import get_schema_context, get_fact_tables, get_dimension_tables

    return {
        "schema_context": get_schema_context(),
        "tables": {
            "fact": get_fact_tables(),
            "dimensions": get_dimension_tables()
        }
    }


@app.get("/anomalies/all")
async def detect_all_anomalies():
    """
    Detect all types of anomalies in data

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
    Detect time series anomalies in data

    Identifies unusual spikes or drops over time using
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

    Identifies outliers across different dimensions (products, customers, etc.)
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

    Identifies sudden spikes or drops for each dimension value.
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


@app.get("/anomalies/prophet")
async def detect_prophet(
    metric: str = Query("SalesAmount", description="Metric to analyze: SalesAmount, OrderQuantity"),
    lookback_days: int = Query(90, description="Historical days to analyze", ge=14, le=730),
    forecast_days: int = Query(30, description="Days to forecast into future", ge=1, le=90)
):
    """
    Detect anomalies using Prophet forecasting (AI-powered)

    Advanced anomaly detection that:
    - Automatically detects weekly and yearly seasonality
    - Identifies trend changes
    - Forecasts expected values
    - Flags values outside 95% confidence interval
    - Provides future forecasts

    More accurate than simple statistical methods because it accounts for:
    - Business trends (growth/decline)
    - Seasonal patterns (weekday vs weekend, monthly cycles)
    - Holiday effects (if configured)

    Example: A Monday with high sales might not be anomalous if
    Mondays are typically high-sales days.
    """
    try:
        # Check cache first
        from services.cache_service import get_cache_service
        cache = get_cache_service()

        cache_params = {
            "metric": metric,
            "lookback": lookback_days,
            "forecast": forecast_days
        }
        cached_result = cache.get_anomaly_cache("prophet", cache_params)

        if cached_result:
            cached_result["cached"] = True
            return cached_result

        # Run detection
        result = anomaly_detector.detect_prophet_anomalies(
            metric=metric,
            lookback_days=lookback_days,
            forecast_days=forecast_days
        )

        result["cached"] = False

        # Cache result (1 hour)
        cache.set_anomaly_cache("prophet", cache_params, result, ttl=3600)

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
        from services.schema_context import get_fact_tables
        fact_tables = get_fact_tables()
        test_table = fact_tables[0] if fact_tables else "FactInternetSales"
        result = rag_service.execute_query(f"SELECT TOP 1 1 AS test FROM {test_table}", limit=1)
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


# Performance & Cache Management Endpoints

@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics

    Shows hit rate, backend type (Redis/memory), and cache metrics.
    """
    try:
        from services.cache_service import get_cache_service
        cache = get_cache_service()
        return cache.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/clear")
async def clear_cache(cache_type: str = Query(None, description="Cache type: query, anomaly, or all")):
    """
    Clear cache

    Args:
        cache_type: Type of cache to clear (query, anomaly, all)
    """
    try:
        from services.cache_service import get_cache_service
        cache = get_cache_service()

        if cache_type == "query":
            count = cache.clear_query_cache()
        elif cache_type == "anomaly":
            count = cache.clear_anomaly_cache()
        else:
            count = cache.clear()

        return {
            "success": True,
            "keys_deleted": count,
            "cache_type": cache_type or "all"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pool/stats")
async def get_connection_pool_stats():
    """
    Get database connection pool statistics

    Shows pool size, active connections, and hit rate.
    """
    try:
        from services.db_pool import get_connection_pool
        pool = get_connection_pool()
        return pool.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Vector Store Management Endpoints

class QueryExampleRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    sql: str = Field(..., description="SQL query")
    intent: str = Field("general_query", description="Query intent/category")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SemanticSearchRequest(BaseModel):
    question: str = Field(..., description="Question to search for")
    n_results: int = Field(5, description="Number of results", ge=1, le=20)
    intent_filter: Optional[str] = Field(None, description="Filter by intent")


@app.post("/vector-store/add")
async def add_query_example(request: QueryExampleRequest):
    """
    Add a query example to the vector store

    This allows you to teach the system new query patterns.
    The example will be used for semantic search when generating SQL.
    """
    try:
        from services.vector_store import get_vector_store
        vector_store = get_vector_store()

        doc_id = vector_store.add_query_example(
            question=request.question,
            sql=request.sql,
            intent=request.intent,
            metadata=request.metadata
        )

        return {
            "success": True,
            "doc_id": doc_id,
            "message": "Query example added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vector-store/search")
async def search_similar_queries(request: SemanticSearchRequest):
    """
    Search for similar queries using semantic search

    This endpoint shows which example queries are most similar
    to your question. Useful for debugging and understanding
    how the RAG system selects examples.
    """
    try:
        from services.vector_store import get_vector_store
        vector_store = get_vector_store()

        results = vector_store.search_similar_queries(
            question=request.question,
            n_results=request.n_results,
            intent_filter=request.intent_filter
        )

        return {
            "question": request.question,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vector-store/stats")
async def get_vector_store_stats():
    """
    Get statistics about the vector store

    Shows total examples, intents distribution, and embedding model info.
    """
    try:
        from services.vector_store import get_vector_store
        vector_store = get_vector_store()

        stats = vector_store.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vector-store/examples")
async def get_all_examples():
    """
    Get all query examples from the vector store

    Returns all stored query examples with their metadata.
    """
    try:
        from services.vector_store import get_vector_store
        vector_store = get_vector_store()

        examples = vector_store.get_all_examples()
        return {
            "examples": examples,
            "count": len(examples)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/vector-store/example/{doc_id}")
async def delete_example(doc_id: str):
    """
    Delete a query example from the vector store

    Args:
        doc_id: Document ID to delete
    """
    try:
        from services.vector_store import get_vector_store
        vector_store = get_vector_store()

        success = vector_store.delete_example(doc_id)

        if success:
            return {"success": True, "message": f"Example {doc_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Example not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vector-store/initialize")
async def initialize_vector_store():
    """
    Initialize vector store with example queries

    This will clear existing examples and load the default
    example queries from schema_context.py
    """
    try:
        from services.vector_store import get_vector_store

        vector_store = get_vector_store()

        # Clear existing
        vector_store.clear_all()

        # Add examples
        examples = get_example_queries()
        count = vector_store.bulk_add_examples(examples)

        stats = vector_store.get_stats()

        return {
            "success": True,
            "examples_added": count,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    from config.settings import settings

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_PORT,
        reload=True
    )
