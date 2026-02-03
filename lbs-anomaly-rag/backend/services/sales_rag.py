"""RAG Service for Internet Sales Natural Language to SQL"""
import requests
import json
import pyodbc
import pandas as pd
from typing import Dict, List, Any, Optional
from config.settings import settings
from services.schema_context import get_schema_context, get_example_queries


class SalesRAGService:
    """Natural language to SQL query service for Internet Sales data"""

    def __init__(self):
        self.schema_context = get_schema_context()
        self.example_queries = get_example_queries()
        self.llama_url = settings.LLAMA_SERVER_URL
        self.model = settings.LLAMA_MODEL

    def _get_db_connection(self):
        """Get database connection"""
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
        # Build few-shot examples
        examples_text = "\n\n".join([
            f"Question: {ex['question']}\nIntent: {ex['intent']}\nSQL:\n{ex['sql']}"
            for ex in self.example_queries[:5]
        ])

        system_prompt = f"""You are an expert SQL Server query generator for the AdventureWorksDW2019 database.
Your task is to convert natural language questions into accurate T-SQL queries.

{self.schema_context}

IMPORTANT RULES:
1. Generate ONLY valid T-SQL queries for SQL Server
2. Use proper table aliases as documented (sal, cust, prod, dt, st, curr, promo)
3. Always use INNER JOIN unless explicitly asked for other join types
4. For TOP N queries, always include ORDER BY clause
5. Use DimDate.CalendarYear for year filters, not YEAR() function on dates
6. Concatenate customer names as: FirstName + ' ' + LastName
7. Wrap all queries in proper SELECT statements
8. Use SUM() for money columns, not COUNT()
9. Include appropriate GROUP BY for aggregations
10. Return ONLY the SQL query, no explanations or markdown
"""

        prompt = f"""Here are some example questions and their SQL queries:

{examples_text}

Now generate a SQL query for this question:
Question: {question}

Generate the SQL query:"""

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
            "geographic": "analyzes sales by geographic location",
            "promotion": "evaluates promotion effectiveness",
            "general_query": "queries the sales data"
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
        try:
            conn = self._get_db_connection()

            # Add TOP clause if not present and no other limiting clause
            sql_upper = sql.upper().strip()
            if not any(keyword in sql_upper for keyword in ["TOP ", "FETCH ", "OFFSET "]):
                # Insert TOP after SELECT
                if sql_upper.startswith("SELECT"):
                    sql = sql[:6] + f" TOP {limit}" + sql[6:]

            # Execute query
            df = pd.read_sql(sql, conn)
            conn.close()

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

            return {
                "data": data,
                "row_count": len(data),
                "columns": list(df.columns),
                "success": True
            }

        except Exception as e:
            return {
                "data": [],
                "row_count": 0,
                "columns": [],
                "success": False,
                "error": str(e)
            }

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
        # Generate SQL
        generation_result = self.generate_sql(question)

        result = {
            "question": question,
            "sql": generation_result["sql"],
            "intent": generation_result["intent"],
            "explanation": generation_result["explanation"],
        }

        # Execute if requested
        if execute:
            execution_result = self.execute_query(generation_result["sql"], limit)
            result.update(execution_result)

        return result

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
