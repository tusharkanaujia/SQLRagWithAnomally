# Complete Setup Guide - Sales RAG with Anomaly Detection

## System Overview

You now have a comprehensive data intelligence platform with:
- ✅ Natural Language to SQL (RAG) using Llama LLM
- ✅ Advanced anomaly detection (time series, statistical, comparative)
- ✅ Modern React dashboard with Ant Design
- ✅ FastAPI backend with multiple endpoints
- ✅ Connected to AdventureWorksDW2019 database

## Prerequisites Status

- ✅ SQL Server: `IMPOSSIBLEISNOT\MSSQLSERVER2019`
- ✅ Database: `AdventureWorksDW2019` (60,398 sales records)
- ✅ Python dependencies: Installed
- ⚠️ Ollama with Llama: **Needs setup** (see below)
- ✅ React frontend: Configured with Ant Design

## Step-by-Step Setup

### 1. Install and Configure Ollama

Ollama is required for the Natural Language to SQL feature.

**Download and Install:**
1. Visit https://ollama.com/download
2. Download Ollama for Windows
3. Run the installer

**Start Ollama Server:**
```bash
# Open Command Prompt or PowerShell
ollama serve
```

**Install Llama Model:**
Open a NEW terminal and run:
```bash
ollama pull llama3.1
```

This will download the Llama 3.1 model (~4.7GB). Wait for it to complete.

**Verify Installation:**
```bash
ollama list
```

You should see:
```
NAME            ID              SIZE    MODIFIED
llama3.1:latest xxxxx           4.7 GB  X minutes ago
```

### 2. Test the Backend

The backend is already configured and ready to run.

**Start the Backend API:**
```bash
cd backend
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Test the API:**
Open a new terminal and run:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "llm": "healthy"
  }
}
```

### 3. Start the Frontend

The frontend is configured with Ant Design and all components.

**Start the Frontend:**
```bash
cd frontend
npm start
```

The browser will automatically open to `http://localhost:3000`

If not, manually open your browser and go to:
```
http://localhost:3000
```

## Using the Dashboard

### Main Interface

The dashboard has 3 main tabs:

#### 1. SQL Query Tab (Landing Page)

**Features:**
- Natural language input field
- Example questions as clickable tags
- Auto-generated SQL display
- Results table with pagination
- Automatic chart visualization
- CSV export

**Try These Questions:**
```
"What were the total sales in 2013?"
"Who are the top 10 customers by total purchases?"
"Show me the top 10 products by quantity sold"
"What were monthly sales trends in 2013?"
"Show sales by country"
"Which promotions generated the most revenue?"
```

**How It Works:**
1. Type or click an example question
2. Click "Query" button
3. System sends question to Llama LLM
4. LLM generates SQL query
5. SQL is displayed with intent classification
6. Query is executed against database
7. Results are shown in table and chart
8. Export to CSV if needed

#### 2. Anomaly Detection Tab

**Overview Section:**
- Total anomalies detected
- Detection methods used
- Time series anomaly count
- Comparative anomaly count
- Distribution chart by type

**Time Series Tab:**
- Daily sales trend visualization
- Anomaly markers (red dots)
- Confidence bounds (orange shaded area)
- Moving average (green dashed line)
- Anomaly details table with:
  - Date
  - Actual vs Expected values
  - Deviation percentage
  - Type (spike/drop)
  - Severity level

**Comparative (YoY/MoM) Tab:**
- Year-over-Year comparison charts
- Side-by-side bar charts (Current vs Previous)
- Anomaly table showing:
  - Period
  - Current and previous values
  - Percentage change
  - Type (increase/decrease)
  - Severity

**Statistical Tab:**
- Product sales anomalies (Z-Score method)
- Customer purchase anomalies (Isolation Forest)
- Outlier detection with statistical measures

### Dashboard Features

**Visual Indicators:**
- 🔴 Red = High severity anomaly
- 🟠 Orange = Medium severity anomaly
- 🟡 Yellow = Low severity anomaly
- 🟢 Green = No anomaly

**Interactive Elements:**
- Click on example questions to auto-fill
- Hover over charts for detailed tooltips
- Sort and filter tables
- Pagination for large result sets
- Responsive design for mobile/tablet

## API Endpoints Reference

### Query Endpoints

**1. POST /query** - Natural Language Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What were the total sales in 2013?", "execute": true, "limit": 100}'
```

**2. POST /generate-sql** - Generate SQL Only
```bash
curl -X POST "http://localhost:8000/generate-sql?question=Who are the top 10 customers?"
```

**3. GET /examples** - Get Example Queries
```bash
curl http://localhost:8000/examples
```

**4. GET /schema** - Get Database Schema Info
```bash
curl http://localhost:8000/schema
```

### Anomaly Detection Endpoints

**1. GET /anomalies/all** - All Anomaly Types
```bash
curl http://localhost:8000/anomalies/all
```

**2. GET /anomalies/time-series** - Time Series Anomalies
```bash
curl "http://localhost:8000/anomalies/time-series?granularity=daily&lookback_days=30"
```

**3. GET /anomalies/comparative** - Comparative Anomalies
```bash
curl "http://localhost:8000/anomalies/comparative?comparison_type=yoy&threshold_pct=20"
```

**4. GET /anomalies/statistical** - Statistical Anomalies
```bash
curl "http://localhost:8000/anomalies/statistical?dimension=ProductKey&method=zscore"
```

**5. GET /health** - Health Check
```bash
curl http://localhost:8000/health
```

## Interactive API Documentation

Once the backend is running, visit:

**Swagger UI:**
```
http://localhost:8000/docs
```

**ReDoc:**
```
http://localhost:8000/redoc
```

These provide:
- Interactive API testing
- Request/response examples
- Parameter documentation
- Try it out functionality

## Troubleshooting

### Issue 1: Ollama Not Found

**Symptom:**
```
"llm": "unhealthy: Connection refused"
```

**Solution:**
```bash
# Start Ollama in a new terminal
ollama serve

# Verify it's running
ollama list
```

### Issue 2: Model Not Loaded

**Symptom:**
```
"llm": "unhealthy: model not found"
```

**Solution:**
```bash
# Pull the model
ollama pull llama3.1

# Verify
ollama list
```

### Issue 3: Database Connection Error

**Symptom:**
```
"database": "unhealthy: Cannot connect"
```

**Solution:**
```bash
# Run diagnostics
cd backend
python diagnose_connection.py
```

### Issue 4: Frontend Not Connecting

**Symptom:**
Frontend shows connection errors

**Solution:**
1. Ensure backend is running on port 8000
2. Check browser console for errors
3. Verify `proxy` in `frontend/package.json` is set to `http://localhost:8000`
4. Restart frontend:
   ```bash
   cd frontend
   npm start
   ```

### Issue 5: Port Already in Use

**Backend:**
```bash
# Change port in .env
API_PORT=8001

# Restart backend
```

**Frontend:**
```bash
# The frontend will prompt you to use a different port
# Or manually set PORT=3001 before npm start
PORT=3001 npm start
```

## Performance Optimization

### 1. LLM Response Speed

For faster SQL generation:
```bash
# Use a smaller, faster model
ollama pull llama3.1:8b  # Smaller version

# Update .env
LLAMA_MODEL=llama3.1:8b
```

For better accuracy:
```bash
# Use a larger model
ollama pull llama3.1:70b

# Update .env
LLAMA_MODEL=llama3.1:70b
```

### 2. Query Performance

- Use specific questions
- Limit result sets (default is 100 rows)
- Add database indexes on frequently queried columns

### 3. Anomaly Detection Speed

- Reduce `lookback_days` for faster processing
- Use appropriate granularity (daily vs monthly)
- Adjust detection thresholds

## Next Steps

1. **Explore the Dashboard**
   - Try different natural language questions
   - Review anomaly detection results
   - Export data to CSV

2. **Customize**
   - Add more example queries in `backend/services/schema_context.py`
   - Adjust anomaly thresholds in `backend/services/anomaly_detection.py`
   - Customize UI colors in `frontend/src/App.css`

3. **Extend**
   - Add more charts and visualizations
   - Implement user authentication
   - Create scheduled anomaly reports
   - Add email/SMS alerts

## File Locations

**Backend:**
- Main API: `backend/main.py`
- RAG Service: `backend/services/sales_rag.py`
- Anomaly Detection: `backend/services/anomaly_detection.py`
- Schema Context: `backend/services/schema_context.py`
- Configuration: `backend/config/settings.py`
- Environment: `.env`

**Frontend:**
- Main App: `frontend/src/App.js`
- Query Interface: `frontend/src/components/QueryInterface.js`
- Anomaly Dashboard: `frontend/src/components/AnomalyDashboard.js`
- Styling: `frontend/src/App.css`

**Documentation:**
- This guide: `SETUP_GUIDE.md`
- Quick start: `QUICKSTART.md`
- Detailed RAG docs: `README_SALES_RAG.md`

## Summary of What Was Built

✅ **Backend Features:**
1. Natural Language to SQL conversion using Llama LLM
2. Time series anomaly detection (daily, weekly, monthly)
3. Statistical anomaly detection (Z-score, IQR, Isolation Forest)
4. Comparative anomaly detection (YoY, MoM, QoQ)
5. Query validation and execution
6. CSV export capability
7. Health monitoring

✅ **Frontend Features:**
1. Modern dashboard with Ant Design
2. Natural language query interface
3. Real-time SQL generation display
4. Interactive data tables
5. Automatic chart generation (line, bar charts)
6. Comprehensive anomaly dashboard
7. Visual anomaly indicators
8. Responsive design

✅ **Database:**
- Connected to AdventureWorksDW2019
- 60,398 sales records
- 18,484 customers
- 606 products
- All dimension tables

## Support

If you encounter issues:

1. Check backend logs in the terminal where `python main.py` is running
2. Check frontend logs in browser console (F12)
3. Run health check: `curl http://localhost:8000/health`
4. Run database diagnostics: `python backend/diagnose_connection.py`
5. Verify Ollama: `ollama list`

## Success Indicators

You'll know everything is working when:

✅ Backend shows "Application startup complete"
✅ Frontend opens in browser at localhost:3000
✅ Health check returns all "healthy" statuses
✅ Example questions generate SQL and results
✅ Anomaly dashboard shows detection results
✅ Charts and visualizations render properly

**Congratulations! Your Sales RAG with Anomaly Detection system is now fully operational!** 🎉
