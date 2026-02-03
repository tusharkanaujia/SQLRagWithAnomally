# Quick Start Guide - Sales RAG System

Get up and running with the Sales RAG system in 5 minutes!

## Prerequisites

- ✅ SQL Server with AdventureWorksDW2019 database (already configured)
- ✅ Python 3.8+ installed
- ⚠️ Ollama with Llama model (needs setup)

## Step 1: Install Ollama and Llama Model

### Windows

1. Download Ollama from https://ollama.com/download
2. Install Ollama
3. Open Command Prompt and run:
```bash
ollama serve
```

4. In another Command Prompt, install Llama:
```bash
ollama pull llama3.1
```

### Verify Installation
```bash
ollama list
```

You should see `llama3.1` in the list.

## Step 2: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 3: Test Database Connection

```bash
python test_connection.py
```

Expected output:
```
[OK] Connection successful!
FactInternetSales (60,398 rows)
DimCustomer (18,484 rows)
...
```

## Step 4: Start the API Server

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## Step 5: Test Your First Query

Open a new terminal and run:

### Using curl (Windows PowerShell)
```powershell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/query" `
  -ContentType "application/json" `
  -Body '{"question":"What were the total sales in 2013?","execute":true,"limit":10}'
```

### Using curl (Command Prompt with curl)
```bash
curl -X POST http://localhost:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"What were the total sales in 2013?\",\"execute\":true,\"limit\":10}"
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "What were the total sales in 2013?",
        "execute": True,
        "limit": 10
    }
)

print(response.json())
```

## Step 6: Explore the API

### Open Interactive API Documentation

Visit in your browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Try Example Questions

```python
import requests

questions = [
    "Who are the top 5 customers by total purchases?",
    "What products sold the most in quantity?",
    "Show sales by country",
    "What were monthly sales trends in 2013?",
]

for question in questions:
    response = requests.post(
        "http://localhost:8000/query",
        json={"question": question, "execute": True, "limit": 10}
    )
    result = response.json()
    print(f"\nQuestion: {question}")
    print(f"SQL: {result['sql']}")
    print(f"Results: {result['row_count']} rows")
    print("-" * 80)
```

## Common Issues & Solutions

### 1. Ollama Not Running

**Error:** Connection refused to localhost:11434

**Solution:**
```bash
ollama serve
```

### 2. Model Not Found

**Error:** Model llama3.1 not found

**Solution:**
```bash
ollama pull llama3.1
```

### 3. Database Connection Error

**Error:** Cannot connect to SQL Server

**Solution:**
- Ensure SQL Server is running
- Verify instance name in `.env` file
- Check SQL Server Browser service is running

Run diagnostics:
```bash
python diagnose_connection.py
```

### 4. Port Already in Use

**Error:** Port 8000 already in use

**Solution:** Change port in `.env`:
```
API_PORT=8001
```

## Testing the System

### Test RAG Service
```bash
python test_rag.py
```

This will:
- Generate SQL for multiple questions
- Validate the SQL syntax
- Execute queries and show results

### Test API Endpoints
```bash
# Get examples
curl http://localhost:8000/examples

# Get schema info
curl http://localhost:8000/schema

# Health check
curl http://localhost:8000/health
```

## What's Next?

1. **Explore the API**: Try different questions in the Swagger UI
2. **Review the README**: Check [README_SALES_RAG.md](README_SALES_RAG.md) for detailed documentation
3. **Build a Frontend**: Create a web interface to interact with the API
4. **Customize**: Modify schema context and examples in `services/schema_context.py`

## Sample Questions to Try

### Sales Analysis
- "What were the total sales in 2013?"
- "Show me quarterly sales for 2014"
- "What's the average order value?"

### Customer Insights
- "Who are the top 10 customers?"
- "How many customers do we have from each country?"
- "What's the average income of our customers?"

### Product Performance
- "Which products generate the most revenue?"
- "Show me the top 5 products by quantity sold"
- "What's the most expensive product?"

### Geographic Analysis
- "Show sales by territory"
- "Which country has the highest sales?"
- "Compare sales across different regions"

### Trends
- "Show monthly sales trends in 2013"
- "What were the best-selling months?"
- "Compare Q1 vs Q2 sales"

## Architecture Overview

```
Your Question
     ↓
FastAPI Server (localhost:8000)
     ↓
Sales RAG Service
     ↓
Llama LLM (Ollama) → Generates SQL
     ↓
SQL Server (AdventureWorksDW2019) → Executes Query
     ↓
Results (JSON)
```

## Support

If you encounter issues:

1. Check the logs in the terminal where you ran `python main.py`
2. Run diagnostics: `python diagnose_connection.py`
3. Verify Ollama is running: `ollama list`
4. Check API health: `curl http://localhost:8000/health`

## Performance Tips

1. **Use specific questions**: More specific questions generate better SQL
2. **Limit results**: Use the `limit` parameter to avoid large result sets
3. **Cache queries**: The system validates SQL before execution
4. **Better model**: For improved accuracy, try larger models:
   ```bash
   ollama pull llama3.1:70b
   ```
   Then update `.env`: `LLAMA_MODEL=llama3.1:70b`

Enjoy using your Sales RAG system! 🚀
