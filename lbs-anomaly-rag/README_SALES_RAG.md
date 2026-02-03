# Sales RAG System for AdventureWorksDW2019

A complete RAG (Retrieval Augmented Generation) system that converts natural language questions into SQL queries for the AdventureWorksDW2019 database.

## Overview

This system allows you to ask questions about internet sales data in natural language, and it automatically:
1. Converts your question to a SQL query using Llama LLM
2. Executes the query against the AdventureWorksDW2019 database
3. Returns the results in a structured format
4. Suggests appropriate chart types for visualization

## Architecture

```
┌─────────────────┐
│  User Question  │
└────────┬────────┘
         │
         v
┌─────────────────────────────────┐
│  Sales RAG Service              │
│  - Schema Context               │
│  - Few-shot Examples            │
│  - Llama LLM                    │
└────────┬────────────────────────┘
         │
         v
┌─────────────────┐
│  SQL Query      │
└────────┬────────┘
         │
         v
┌─────────────────────────────────┐
│  AdventureWorksDW2019           │
│  - FactInternetSales            │
│  - Dimension Tables             │
└────────┬────────────────────────┘
         │
         v
┌─────────────────┐
│  Results + Data │
└─────────────────┘
```

## Database Schema

### Fact Table
- **FactInternetSales** (60,398 rows): Internet sales transactions

### Dimension Tables
- **DimCustomer** (18,484 rows): Customer demographics
- **DimProduct** (606 rows): Product catalog
- **DimDate** (3,652 rows): Date dimension
- **DimSalesTerritory** (11 rows): Sales territories
- **DimCurrency** (105 rows): Currency information
- **DimPromotion** (16 rows): Promotions and discounts

## Setup

### Prerequisites
1. SQL Server with AdventureWorksDW2019 database
2. Ollama running locally with Llama model
3. Python 3.8+

### Installation

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```bash
DB_SERVER=IMPOSSIBLEISNOT\MSSQLSERVER2019
DB_DATABASE=AdventureWorksDW2019
DB_TRUSTED_CONNECTION=yes
LLAMA_SERVER_URL=http://localhost:11434
LLAMA_MODEL=llama3.1
API_PORT=8000
```

3. Verify database connection:
```bash
python test_connection.py
```

## Usage

### Starting the API Server

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Query Sales Data (POST /query)
Ask questions in natural language and get SQL + results.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What were the total sales in 2013?",
    "execute": true,
    "limit": 100
  }'
```

Response:
```json
{
  "question": "What were the total sales in 2013?",
  "sql": "SELECT SUM(sal.SalesAmount) AS TotalSales FROM FactInternetSales sal INNER JOIN DimDate dt ON dt.DateKey = sal.OrderDateKey WHERE dt.CalendarYear = 2013",
  "intent": "aggregation",
  "explanation": "This query calculates aggregate metrics based on your question",
  "data": [{"TotalSales": 12345678.90}],
  "row_count": 1,
  "columns": ["TotalSales"],
  "success": true,
  "chart_suggestion": {
    "type": "metric",
    "value": "TotalSales"
  }
}
```

#### 2. Generate SQL Only (POST /generate-sql)
Get SQL query without executing it.

```bash
curl -X POST "http://localhost:8000/generate-sql?question=Who are the top 10 customers?"
```

#### 3. Execute SQL Directly (POST /execute-sql)
Execute a SQL query directly.

```bash
curl -X POST "http://localhost:8000/execute-sql?sql=SELECT TOP 5 * FROM FactInternetSales&limit=5"
```

#### 4. Get Examples (GET /examples)
Get example questions and their SQL queries.

```bash
curl http://localhost:8000/examples
```

#### 5. Get Schema Info (GET /schema)
Get database schema documentation.

```bash
curl http://localhost:8000/schema
```

#### 6. Health Check (GET /health)
Check API and dependencies health.

```bash
curl http://localhost:8000/health
```

## Example Questions

### Sales Analysis
- "What were the total sales in 2013?"
- "Show monthly sales trends in 2013"
- "What were sales in the first quarter of 2014?"

### Customer Analysis
- "Who are the top 10 customers by total purchases?"
- "What's the average order value by customer education level?"
- "How many customers from each country?"

### Product Analysis
- "What products sold the most in quantity?"
- "Which product generated the highest revenue?"
- "Show me sales for Mountain Bikes"

### Geographic Analysis
- "Show sales by country"
- "What are sales by territory and region?"
- "Which country has the highest revenue?"

### Promotion Analysis
- "Which promotions generated the most revenue?"
- "What's the impact of discounts on sales?"

### Time Series
- "Show quarterly sales for 2013 and 2014"
- "What were monthly sales trends in 2013?"
- "Compare sales between fiscal years"

## Testing

### Test Database Connection
```bash
cd backend
python test_connection.py
```

### Test RAG Service
```bash
cd backend
python test_rag.py
```

### Diagnose Connection Issues
```bash
cd backend
python diagnose_connection.py
```

## Project Structure

```
backend/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration and environment variables
├── models/
│   ├── __init__.py
│   └── schemas.py           # Pydantic models
├── services/
│   ├── __init__.py
│   ├── schema_context.py    # Database schema documentation for LLM
│   └── sales_rag.py         # RAG service for NL to SQL
├── main.py                  # FastAPI application
├── test_connection.py       # Database connection test
├── test_rag.py             # RAG service tests
├── diagnose_connection.py  # Connection diagnostics
└── requirements.txt        # Python dependencies
```

## How It Works

### 1. Schema Context
The system provides comprehensive schema documentation to the LLM, including:
- Table structures and relationships
- Column names and data types
- Common query patterns
- Important notes and conventions

### 2. Few-Shot Learning
The system includes example questions and their SQL queries to guide the LLM in generating accurate queries.

### 3. SQL Generation
Using Llama (via Ollama), the system:
- Analyzes the natural language question
- Classifies the intent (ranking, aggregation, time series, etc.)
- Generates syntactically correct T-SQL
- Follows best practices and schema conventions

### 4. Query Execution
The generated SQL is:
- Validated for syntax errors
- Executed against the database with appropriate limits
- Results are formatted and returned with metadata

### 5. Chart Suggestions
Based on the query intent and result structure, the system suggests appropriate visualization types:
- **Line charts**: For time series data
- **Bar charts**: For rankings and comparisons
- **Metrics**: For aggregate values

## Configuration

### Database Settings
```bash
DB_SERVER=IMPOSSIBLEISNOT\MSSQLSERVER2019
DB_DATABASE=AdventureWorksDW2019
DB_USERNAME=                     # Leave empty for Windows auth
DB_PASSWORD=                     # Leave empty for Windows auth
DB_TRUSTED_CONNECTION=yes        # Use Windows authentication
```

### LLM Settings
```bash
LLAMA_SERVER_URL=http://localhost:11434
LLAMA_MODEL=llama3.1
```

### API Settings
```bash
API_PORT=8000
QUERY_TIMEOUT_SECONDS=300
MAX_RECORDS_PER_QUERY=1000000
```

## Troubleshooting

### Database Connection Issues

1. **Cannot connect to named instance**:
   - Ensure SQL Server Browser service is running
   - Check SQL Server Configuration Manager for TCP/IP settings
   - Verify instance name is correct

2. **Authentication failed**:
   - For Windows auth, use `DB_TRUSTED_CONNECTION=yes`
   - For SQL auth, provide username and password

3. **Timeout errors**:
   - Increase `QUERY_TIMEOUT_SECONDS` in .env
   - Check network connectivity

### LLM Issues

1. **Llama not responding**:
   - Verify Ollama is running: `ollama serve`
   - Check the model is installed: `ollama list`
   - Test with: `ollama run llama3.1`

2. **Poor SQL quality**:
   - Try a more powerful model (e.g., llama3.1:70b)
   - Adjust temperature in `sales_rag.py` (lower = more deterministic)
   - Add more few-shot examples

### SQL Generation Issues

1. **Incorrect SQL syntax**:
   - Check the schema context documentation
   - Verify table and column names in the database
   - Review the few-shot examples

2. **Query returns no results**:
   - Check date ranges in the database
   - Verify filter conditions are appropriate
   - Test the generated SQL directly in SSMS

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Next Steps

1. **Frontend Development**: Build a React/Next.js frontend to provide a user-friendly interface
2. **Query History**: Store and track previously asked questions
3. **Query Optimization**: Add query plan analysis and optimization suggestions
4. **Advanced Analytics**: Implement statistical analysis and anomaly detection
5. **Export Features**: Add CSV, Excel, and PDF export capabilities
6. **Visualization**: Integrate with charting libraries (Chart.js, D3.js)
7. **Multi-Model Support**: Support for other LLMs (OpenAI, Anthropic)

## License

This project is for educational and demonstration purposes.
