# Troubleshooting Guide

This guide covers common installation and runtime issues you may encounter with the LBS Anomaly RAG system.

## Installation Issues

### 1. Windows: numpy Build Error (No C Compiler)

**Error Message:**
```
error: Microsoft Visual C++ 14.0 or greater is required
Unknown compiler(s): [['icl'], ['cl'], ['cc'], ['gcc'], ['clang'], ['clang-cl']]
ERROR: Could not build wheels for numpy, which is required to install pyproject.toml-based projects
```

**Cause:**
- numpy (and dependencies like chromadb) try to build from source
- Windows doesn't have a C compiler (MSVC, gcc, or clang) installed by default
- Building scientific packages from source on Windows requires Visual Studio Build Tools

**Solutions:**

#### Option 1: Use Pre-built Wheels (Recommended for Windows)

Install packages using only pre-built binary wheels (no compilation needed):

```bash
# Install core dependencies with pre-built wheels
pip install --only-binary :all: numpy pandas scipy scikit-learn

# Install chromadb and sentence-transformers with pre-built wheels
pip install --only-binary :all: chromadb sentence-transformers

# Install remaining dependencies
pip install -r requirements.txt
```

**Pros:**
- ✅ No compiler needed
- ✅ Fast installation
- ✅ Most reliable on Windows

**Cons:**
- ❌ May not work for very new Python versions or uncommon platforms

#### Option 2: Use Conda (Best for Windows Data Science)

Conda provides pre-compiled packages optimized for Windows:

```bash
# Install Anaconda or Miniconda first
# Download from: https://www.anaconda.com/products/distribution

# Create new environment
conda create -n lbs-anomaly python=3.10

# Activate environment
conda activate lbs-anomaly

# Install packages via conda (pre-compiled)
conda install -c conda-forge fastapi uvicorn pandas numpy scipy scikit-learn redis-py

# Install remaining packages via pip
pip install chromadb sentence-transformers prophet pyodbc sqlparse python-multipart
```

**Pros:**
- ✅ Best for Windows
- ✅ Handles complex dependencies automatically
- ✅ Optimized binary packages

**Cons:**
- ❌ Requires Anaconda/Miniconda installation
- ❌ Larger download size

#### Option 3: Minimal Installation (Skip Optional Features)

If you don't need vector search, caching, or Prophet:

```bash
# Install only core dependencies (no chromadb, redis, or prophet)
pip install fastapi uvicorn pandas pyodbc sqlparse python-multipart python-dotenv pydantic
```

**What you'll lose:**
- ❌ Vector-based RAG (semantic search)
- ❌ Redis caching (falls back to in-memory)
- ❌ Prophet anomaly detection

**What still works:**
- ✅ Basic text-to-SQL queries
- ✅ In-memory caching
- ✅ Statistical anomaly detection (Z-score, day-on-day, comparative)

#### Option 4: Install Visual Studio Build Tools (Full Installation)

For complete compatibility, install Microsoft's C++ compiler:

1. **Download Visual Studio Build Tools:**
   - Visit: https://visualstudio.microsoft.com/downloads/
   - Scroll to "All Downloads" → "Tools for Visual Studio"
   - Download "Build Tools for Visual Studio 2022"

2. **Install C++ Build Tools:**
   - Run the installer
   - Select "Desktop development with C++"
   - Check these components:
     - MSVC v143 - VS 2022 C++ x64/x86 build tools
     - Windows SDK
   - Install (requires ~6GB disk space)

3. **Restart your computer**

4. **Install packages normally:**
   ```bash
   pip install -r requirements.txt
   ```

**Pros:**
- ✅ Full compatibility with all packages
- ✅ Can compile from source if needed

**Cons:**
- ❌ Large download (~6GB)
- ❌ Slow installation
- ❌ Overkill if you only need Python packages

### 2. ModuleNotFoundError: No module named 'chromadb'

**Error Message:**
```
ModuleNotFoundError: No module named 'chromadb'
```

**Cause:**
- chromadb not installed
- Virtual environment not activated
- Dependencies not installed

**Solutions:**

```bash
# Ensure you're in the backend directory
cd backend

# Activate virtual environment (if using one)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install chromadb specifically
pip install chromadb sentence-transformers
```

### 3. Redis Connection Error

**Error Message:**
```
⚠ Redis unavailable: [Errno 111] Connection refused
  Using in-memory cache (not persisted)
```

**Cause:**
- Redis server not running
- Redis not installed

**Solutions:**

**Option 1: Install and Start Redis**

Windows:
```bash
# Using Chocolatey
choco install redis-64

# Or download from:
# https://github.com/microsoftarchive/redis/releases

# Start Redis
redis-server
```

Linux/Mac:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Mac
brew install redis
brew services start redis
```

**Option 2: Use In-Memory Cache (No Redis)**

The system automatically falls back to in-memory caching if Redis is unavailable. This works fine but:
- ❌ Cache is lost when server restarts
- ❌ Not shared across multiple instances

To verify it's working:
```bash
GET http://localhost:8000/cache/stats
```

Response will show:
```json
{
  "backend": "memory",
  "hits": 0,
  "misses": 0,
  ...
}
```

### 4. Prophet Installation Issues

**Error Message:**
```
ERROR: Failed building wheel for prophet
```

**Solutions:**

**Windows:**
```bash
# Use conda (recommended)
conda install -c conda-forge prophet

# Or use pre-built wheel
pip install --only-binary :all: prophet
```

**Linux/Mac:**
```bash
# Install dependencies first
# Ubuntu/Debian:
sudo apt-get install python3-dev build-essential

# Mac:
xcode-select --install

# Then install prophet
pip install prophet
```

**Skip Prophet (if not needed):**

Edit [requirements.txt](requirements.txt) and comment out:
```bash
# prophet>=1.1.5
# statsmodels>=0.14.0
```

You'll lose Prophet anomaly detection but other features still work.

### 5. pyodbc Connection Error

**Error Message:**
```
pyodbc.Error: ('01000', "[01000] [Microsoft][ODBC Driver Manager] Data source name not found...")
```

**Cause:**
- SQL Server ODBC driver not installed
- Incorrect connection string
- SQL Server not accessible

**Solutions:**

1. **Install ODBC Driver for SQL Server:**

   Windows:
   - Download from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
   - Install "ODBC Driver 17 for SQL Server" or newer

   Linux:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install unixodbc-dev
   ```

   Mac:
   ```bash
   brew install unixodbc
   ```

2. **Verify Connection String:**

   Check [.env](.env):
   ```bash
   DB_SERVER=your-server.database.windows.net
   DB_NAME=your-database
   DB_USERNAME=your-username
   DB_PASSWORD=your-password
   ```

3. **Test Connection:**
   ```bash
   python -c "import pyodbc; print(pyodbc.drivers())"
   ```

   Should show available drivers like:
   ```
   ['SQL Server', 'ODBC Driver 17 for SQL Server', ...]
   ```

## Runtime Issues

### 1. Slow First Query

**Symptom:**
- First API request takes 5-15 seconds
- Subsequent requests are faster

**Cause:**
- Loading embedding models (sentence-transformers)
- Initializing ChromaDB
- Creating database connection pool

**Expected Behavior:**
- First request: 5-15 seconds (model loading)
- Second request: 0.5-2 seconds (query execution)
- Third+ request: 10-100ms (if cached)

**Solution:**
This is normal. Consider:
- Pre-warming models at startup
- Using smaller embedding models
- Caching initialization

### 2. Memory Usage Issues

**Symptom:**
- High memory usage (>2GB)
- Out of memory errors

**Causes:**
- Embedding models loaded in memory (~400MB)
- ChromaDB vector store
- Large query result caches

**Solutions:**

1. **Use Smaller Embedding Model:**

   Edit [services/vector_store.py:21](services/vector_store.py#L21):
   ```python
   # Change from:
   self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 80MB

   # To:
   self.embedding_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 60MB
   ```

2. **Limit Cache Size:**

   Edit [services/cache_service.py:126](services/cache_service.py#L126):
   ```python
   # Reduce max in-memory cache size
   if len(self.memory_cache) > 100:  # Was 1000
       self._cleanup_memory_cache()
   ```

3. **Disable Vector Store (if not needed):**

   In [services/rag_service.py](services/rag_service.py):
   ```python
   rag_service = RAGService(use_vector_search=False)
   ```

### 3. Cache Not Working

**Symptom:**
- Every query takes full execution time
- Cache hit rate is 0%

**Check:**

1. **Verify Cache is Enabled:**
   ```bash
   GET http://localhost:8000/cache/stats
   ```

2. **Check TTL (Time To Live):**
   - Query cache: 5 minutes (300 seconds)
   - Anomaly cache: 1 hour (3600 seconds)
   - If queries are >5 minutes apart, cache will expire

3. **Query Parameters Must Match Exactly:**
   ```bash
   # These are DIFFERENT cache entries:
   GET /query?question=top customers
   GET /query?question=top%20customers
   GET /query?question=Top customers
   ```

4. **Clear and Rebuild Cache:**
   ```bash
   DELETE http://localhost:8000/cache/clear
   ```

### 4. Connection Pool Exhausted

**Error Message:**
```
No database connections available after 5s (max=10)
```

**Cause:**
- Too many concurrent requests
- Connections not being returned to pool
- Long-running queries

**Solutions:**

1. **Increase Pool Size:**

   Edit [services/db_pool.py:229](services/db_pool.py#L229):
   ```python
   _connection_pool = DatabaseConnectionPool(
       min_connections=5,   # Increase from 2
       max_connections=20   # Increase from 10
   )
   ```

2. **Check Pool Statistics:**
   ```bash
   GET http://localhost:8000/pool/stats
   ```

   Healthy pool:
   ```json
   {
     "pool_size": 8,            // Should be > 0
     "active_connections": 2,   // Should be < max
     "pool_hit_rate": 95.0     // Should be > 80%
   }
   ```

3. **Monitor for Connection Leaks:**
   - Ensure all queries properly return connections
   - Use `with PooledConnection(pool) as conn:` pattern

### 5. Prophet Detection Very Slow

**Symptom:**
- `/anomalies/prophet` takes 30+ seconds
- High CPU usage during detection

**Causes:**
- Large lookback period (365+ days)
- Prophet model fitting is CPU-intensive

**Solutions:**

1. **Reduce Lookback Days:**
   ```bash
   # Instead of:
   GET /anomalies/prophet?lookback_days=365

   # Use:
   GET /anomalies/prophet?lookback_days=90
   ```

2. **Use Caching:**
   - Prophet results are cached for 1 hour
   - First request: 10-30 seconds
   - Subsequent requests: <50ms

3. **Run in Background:**
   - Set up scheduled job to run Prophet hourly
   - Cache results for real-time access

## Performance Optimization

### Recommended Settings

**For Development:**
```python
# Small pool, short TTL for testing
DB_POOL_MIN=2
DB_POOL_MAX=5
CACHE_QUERY_TTL=60      # 1 minute
CACHE_ANOMALY_TTL=300   # 5 minutes
```

**For Production (low traffic):**
```python
DB_POOL_MIN=2
DB_POOL_MAX=10
CACHE_QUERY_TTL=300     # 5 minutes
CACHE_ANOMALY_TTL=3600  # 1 hour
```

**For Production (high traffic):**
```python
DB_POOL_MIN=10
DB_POOL_MAX=30
CACHE_QUERY_TTL=600     # 10 minutes
CACHE_ANOMALY_TTL=7200  # 2 hours
```

## Health Checks

### Verify System Health

```bash
# Check API health
GET http://localhost:8000/health

# Check cache status
GET http://localhost:8000/cache/stats

# Check connection pool
GET http://localhost:8000/pool/stats

# Check vector store
GET http://localhost:8000/vector-store/stats
```

### Expected Healthy Response

[health](main.py):
```json
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "llm": "healthy",
    "cache": "redis",
    "pool": "active"
  }
}
```

## Getting Help

### Debug Mode

Enable detailed logging by setting environment variable:
```bash
# .env
LOG_LEVEL=DEBUG
```

### Common Log Messages

**Normal:**
```
✓ Redis cache enabled at redis://localhost:6379/0
✓ Connection pool initialized with 2 connections
✓ Vector store initialized with 150 examples
```

**Warnings (OK):**
```
⚠ Redis unavailable: Connection refused
  Using in-memory cache (not persisted)
```

**Errors (Need attention):**
```
❌ Database connection failed: Login failed
❌ No database connections available
❌ Prophet not installed
```

### Report Issues

If you encounter issues not covered here:

1. Check logs for error messages
2. Verify all dependencies installed: `pip list`
3. Check health endpoints
4. Review configuration in `.env`
5. Test minimal configuration (disable optional features)

## Related Documentation

- [Installation Guide](README.md) - Initial setup instructions
- [Performance Guide](README_PERFORMANCE.md) - Caching and optimization
- [Prophet Guide](README_PROPHET.md) - Anomaly detection setup
- [Vector Store Guide](README_VECTOR_STORE.md) - RAG system setup
