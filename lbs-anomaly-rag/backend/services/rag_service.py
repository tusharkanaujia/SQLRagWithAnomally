"""RAG Service for Natural Language to SQL"""
import requests
import json
import pyodbc
import pandas as pd
from typing import Dict, List, Any, Optional
from config.settings import settings
from services.schema_context import get_schema_context, get_example_queries


class RAGService:
    """Natural language to SQL query service for data warehouse"""

    def __init__(self, use_vector_search: bool = True, use_cache: bool = True):
        self.schema_context = get_schema_context()
        self.example_queries = get_example_queries()
        self.llama_url = settings.LLAMA_SERVER_URL
        self.model = settings.LLAMA_MODEL
        self.use_vector_search = use_vector_search
        self.use_cache = use_cache

        # Initialize cache if enabled
        self.cache = None
        if self.use_cache:
            try:
                from services.cache_service import get_cache_service
                self.cache = get_cache_service()
            except Exception as e:
                print(f"[WARN] Cache initialization failed: {e}")
                self.use_cache = False

        # Initialize vector store if enabled
        self.vector_store = None
        if self.use_vector_search:
            try:
                from services.vector_store import get_vector_store
                self.vector_store = get_vector_store()
                print("[OK] Vector store enabled for semantic search")
            except Exception as e:
                print(f"[WARN] Vector store initialization failed: {e}")
                print("  Falling back to hardcoded examples")
                self.use_vector_search = False

    def _get_db_connection(self):
        """Get database connection from pool"""
        try:
            from services.db_pool import get_connection_pool
            pool = get_connection_pool()
            return pool.get_connection()
        except Exception:
            # Fallback to direct connection
            conn_str = settings.get_db_connection_string()
            return pyodbc.connect(conn_str, timeout=settings.QUERY_TIMEOUT)

    def _call_llama(self, prompt: str, system_prompt: str = None) -> str:
        """Call Llama API for text generation"""
        try:
            url = f"{self.llama_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for more deterministic SQL
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "").strip()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling Llama API: {e}")

    def generate_sql(self, question: str) -> Dict[str, Any]:
        """
        Generate SQL query from natural language question

        Args:
            question: Natural language question

        Returns:
            Dictionary with sql, intent, and explanation
        """
        # Get relevant examples using semantic search or fallback to hardcoded
        if self.use_vector_search and self.vector_store:
            try:
                # Use semantic search to find similar queries
                similar_examples = self.vector_store.search_similar_queries(
                    question=question,
                    n_results=5
                )
                examples_to_use = similar_examples
            except Exception as e:
                print(f"[WARN] Vector search failed: {e}, using hardcoded examples")
                examples_to_use = self.example_queries[:5]
        else:
            # Use first 5 hardcoded examples
            examples_to_use = self.example_queries[:5]

        # Build few-shot examples text
        examples_text = "\n\n".join([
            f"Question: {ex['question']}\nIntent: {ex.get('intent', 'general_query')}\nSQL:\n{ex.get('sql', '')}"
            for ex in examples_to_use
        ])

        system_prompt = f"""You are an expert SQL Server query generator for the AdventureWorksDW2019 database.
Your task is to convert natural language questions into accurate T-SQL queries.

{self.schema_context}

EXAMPLE QUERIES:
{examples_text}

RULES:
1. Return ONLY the raw SQL query. No markdown, no explanations, no semicolons, no code fences.
2. Use table aliases: sal (FactInternetSales), cust (DimCustomer), prod (DimProduct), dt (DimDate), st (DimSalesTerritory), curr (DimCurrency), promo (DimPromotion).
3. Always INNER JOIN every table you reference. If you use dt.CalendarYear, you MUST have "INNER JOIN DimDate dt ON dt.DateKey = sal.OrderDateKey" in your query.
4. Never reference a table alias that is not in your FROM or JOIN clauses.
5. For TOP N queries, always include ORDER BY.
6. Use DimDate.CalendarYear for year filters, not YEAR() on date columns.
7. Customer full name: cust.FirstName + ' ' + cust.LastName
8. Use SUM() for money columns (SalesAmount, etc.), not COUNT().
9. Include GROUP BY for all non-aggregated columns in SELECT.
10. "Last year" means the maximum CalendarYear in the data: use (SELECT MAX(CalendarYear) FROM DimDate dt2 INNER JOIN FactInternetSales s2 ON s2.OrderDateKey = dt2.DateKey).

COMMON MISTAKES TO AVOID:
- Using dt.CalendarYear without joining DimDate
- Using st.SalesTerritoryCountry without joining DimSalesTerritory
- Forgetting GROUP BY when using aggregates with other columns
- Using COUNT() instead of SUM() for SalesAmount
"""

        prompt = f"""Question: {question}

SQL:"""

        # Get SQL from LLM
        sql_response = self._call_llama(prompt, system_prompt)

        # Clean up the response
        sql_query = self._extract_sql(sql_response)

        # Determine intent
        intent = self._classify_intent(question)

        # Generate explanation
        explanation = self._generate_explanation(question, sql_query, intent)

        return {
            "sql": sql_query,
            "intent": intent,
            "explanation": explanation
        }

    def _retry_with_error(self, question: str, failed_sql: str, error: str) -> str:
        """Ask the LLM to fix a failed SQL query based on the error message"""
        system_prompt = f"""You are an expert SQL Server query fixer. A query failed with an error.
Fix the SQL query so it runs correctly. Return ONLY the corrected raw SQL. No markdown, no explanations, no semicolons.

{self.schema_context}

CRITICAL: Every table alias you reference MUST appear in a FROM or JOIN clause.
"""

        prompt = f"""The following SQL query failed:

{failed_sql}

Error message: {error}

Original question: {question}

Write the corrected SQL query:"""

        response = self._call_llama(prompt, system_prompt)
        return self._extract_sql(response)

    def _extract_sql(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Remove markdown code blocks
        sql = response.strip()

        if "```sql" in sql:
            sql = sql.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql:
            sql = sql.split("```")[1].split("```")[0].strip()

        # Remove any leading/trailing whitespace
        sql = sql.strip()

        # Remove any explanatory text before SELECT
        if "SELECT" in sql.upper():
            select_idx = sql.upper().find("SELECT")
            sql = sql[select_idx:]

        return sql

    def _classify_intent(self, question: str) -> str:
        """Classify the intent of the question"""
        question_lower = question.lower()

        if any(word in question_lower for word in ["top", "best", "highest", "most", "largest"]):
            return "ranking"
        elif any(word in question_lower for word in ["total", "sum", "aggregate"]):
            return "aggregation"
        elif any(word in question_lower for word in ["trend", "over time", "monthly", "yearly", "growth"]):
            return "time_series"
        elif any(word in question_lower for word in ["customer", "who", "buyer"]):
            return "customer_analysis"
        elif any(word in question_lower for word in ["product", "item", "sold"]):
            return "product_analysis"
        elif any(word in question_lower for word in ["country", "territory", "region", "geographic"]):
            return "geographic"
        elif any(word in question_lower for word in ["promotion", "discount", "campaign"]):
            return "promotion"
        else:
            return "general_query"

    def _generate_explanation(self, question: str, sql: str, intent: str) -> str:
        """Generate a simple explanation of what the query does"""
        intent_descriptions = {
            "ranking": "ranks and identifies top performers",
            "aggregation": "calculates aggregate metrics",
            "time_series": "analyzes trends over time",
            "customer_analysis": "analyzes customer behavior and demographics",
            "product_analysis": "examines product performance",
            "geographic": "analyzes data by geographic location",
            "promotion": "evaluates promotion effectiveness",
            "general_query": "queries the data warehouse"
        }

        description = intent_descriptions.get(intent, "queries the database")
        return f"This query {description} based on your question: '{question}'"

    def execute_query(self, sql: str, limit: int = 100) -> Dict[str, Any]:
        """
        Execute SQL query and return results

        Args:
            sql: SQL query to execute
            limit: Maximum number of rows to return

        Returns:
            Dictionary with data, row_count, and columns
        """
        # Add TOP clause if not present and no other limiting clause
        sql_upper = sql.upper().strip()
        if not any(keyword in sql_upper for keyword in ["TOP ", "FETCH ", "OFFSET "]):
            if sql_upper.startswith("SELECT"):
                sql = sql[:6] + f" TOP {limit}" + sql[6:]

        # Check SQL-level cache first (same SQL = same results, regardless of question)
        if self.use_cache and self.cache:
            cached = self.cache.get_sql_cache(sql)
            if cached:
                cached["sql_cache_hit"] = True
                return cached

        conn = None
        try:
            conn = self._get_db_connection()

            # Execute query
            df = pd.read_sql(sql, conn)

            # Convert to list of dictionaries
            data = df.to_dict('records')

            # Convert any non-serializable types
            for row in data:
                for key, value in row.items():
                    if pd.isna(value):
                        row[key] = None
                    elif hasattr(value, 'isoformat'):  # datetime
                        row[key] = value.isoformat()
                    elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                        row[key] = str(value)

            result = {
                "data": data,
                "row_count": len(data),
                "columns": list(df.columns),
                "success": True
            }

            # Cache successful SQL results (1 hour - AdventureWorks data is static)
            if self.use_cache and self.cache:
                self.cache.set_sql_cache(sql, result, ttl=3600)

            return result

        except Exception as e:
            return {
                "data": [],
                "row_count": 0,
                "columns": [],
                "success": False,
                "error": str(e)
            }
        finally:
            # Return connection to pool
            if conn:
                try:
                    from services.db_pool import get_connection_pool
                    pool = get_connection_pool()
                    pool.return_connection(conn)
                except Exception:
                    # Fallback: just close it
                    try:
                        conn.close()
                    except Exception:
                        pass

    def query(self, question: str, execute: bool = True, limit: int = 100) -> Dict[str, Any]:
        """
        Complete RAG pipeline: question -> SQL -> results

        Args:
            question: Natural language question
            execute: Whether to execute the query
            limit: Maximum rows to return

        Returns:
            Dictionary with SQL, data, and metadata
        """
        # Check cache first
        if self.use_cache and self.cache:
            cached_result = self.cache.get_query_cache(question, execute)
            if cached_result:
                cached_result["cached"] = True
                return cached_result

        # Generate SQL
        generation_result = self.generate_sql(question)

        result = {
            "question": question,
            "sql": generation_result["sql"],
            "intent": generation_result["intent"],
            "explanation": generation_result["explanation"],
            "cached": False,
            "retries": 0
        }

        # Execute if requested, with self-correction retry loop
        if execute:
            current_sql = generation_result["sql"]
            max_retries = 2

            for attempt in range(max_retries + 1):
                execution_result = self.execute_query(current_sql, limit)

                if execution_result["success"]:
                    result.update(execution_result)
                    result["sql"] = current_sql
                    result["retries"] = attempt
                    break

                # Failed - try to self-correct if retries remain
                if attempt < max_retries:
                    print(f"[RETRY] SQL failed (attempt {attempt + 1}), asking LLM to fix: {execution_result['error'][:100]}")
                    try:
                        current_sql = self._retry_with_error(
                            question=question,
                            failed_sql=current_sql,
                            error=execution_result["error"]
                        )
                        result["retries"] = attempt + 1
                    except Exception as e:
                        print(f"[WARN] Self-correction failed: {e}")
                        result.update(execution_result)
                        break
                else:
                    # All retries exhausted
                    result.update(execution_result)

        # Auto-learn: add successful queries to vector store
        if execute and result.get("success") and self.vector_store:
            try:
                self._auto_learn(question, result["sql"], result["intent"])
            except Exception as e:
                print(f"[WARN] Auto-learn failed: {e}")

        # Cache the result (1 hour for executed queries, 2 hours for SQL-only)
        # AdventureWorks data is static, so longer TTLs are safe
        if self.use_cache and self.cache:
            ttl = 3600 if execute else 7200
            self.cache.set_query_cache(question, result, execute, ttl)

        return result

    def _auto_learn(self, question: str, sql: str, intent: str):
        """Add successful query to vector store if it's sufficiently novel"""
        if not self.vector_store:
            return

        # Check if a very similar question already exists
        similar = self.vector_store.search_similar_queries(question, n_results=1)
        if similar and similar[0]["distance"] < 0.1:
            return  # Too similar to existing example, skip

        self.vector_store.add_query_example(
            question=question,
            sql=sql,
            intent=intent,
            metadata={"source": "auto_learn"}
        )

    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL query without executing it

        Args:
            sql: SQL query to validate

        Returns:
            Dictionary with validation status and messages
        """
        try:
            conn = self._get_db_connection()
            cursor = conn.cursor()

            # Use SET NOEXEC ON to parse without executing
            cursor.execute("SET NOEXEC ON")
            cursor.execute(sql)
            cursor.execute("SET NOEXEC OFF")

            conn.close()

            return {
                "valid": True,
                "message": "SQL query is valid"
            }

        except Exception as e:
            return {
                "valid": False,
                "message": str(e)
            }

    def get_chart_suggestion(self, intent: str, columns: List[str], data: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Suggest appropriate chart type based on query intent and results

        Args:
            intent: Query intent classification
            columns: Column names from query result
            data: Query result data

        Returns:
            Chart configuration suggestion or None
        """
        if not data or not columns:
            return None

        chart_config = {
            "time_series": {
                "type": "line",
                "x": self._find_column(columns, ["year", "month", "date", "quarter"]),
                "y": self._find_column(columns, ["sales", "revenue", "amount", "total"])
            },
            "ranking": {
                "type": "bar",
                "x": self._find_column(columns, ["name", "product", "customer", "country", "region"]),
                "y": self._find_column(columns, ["sales", "revenue", "amount", "total", "count", "quantity"])
            },
            "geographic": {
                "type": "bar",
                "x": self._find_column(columns, ["country", "region", "territory"]),
                "y": self._find_column(columns, ["sales", "revenue", "amount", "total"])
            },
            "aggregation": {
                "type": "metric",
                "value": self._find_column(columns, ["total", "sales", "amount", "revenue"])
            }
        }

        return chart_config.get(intent)

    def _find_column(self, columns: List[str], keywords: List[str]) -> Optional[str]:
        """Find first column matching any keyword"""
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in keywords):
                return col
        return columns[0] if columns else None
