import os
import json
import time
from typing import Dict, Any, List, Optional
import snowflake.connector
from app.config import get_settings
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

settings = get_settings()

class AnalysisAgent:
    """AI-powered analysis agent that queries Snowflake and generates insights"""
    
    def __init__(self):
        self.last_request_time = 0
        self.min_request_interval = 2.0
        
        self.use_snowflake = all([
            settings.snowflake_account,
            settings.snowflake_user,
            settings.snowflake_password
        ])
        
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.use_gemini = True
            print(f"🔑 Using Gemini 2.0 Flash - API Key: {settings.gemini_api_key[:10]}...")
        else:
            self.use_gemini = False
            
        print(f"✅ Analysis Agent initialized (Snowflake: {self.use_snowflake}, AI: {self.use_gemini})")
    
    def get_snowflake_connection(self):
        """Get Snowflake connection"""
        if not self.use_snowflake:
            raise ValueError("Snowflake not configured")
        
        return snowflake.connector.connect(
            user=settings.snowflake_user,
            password=settings.snowflake_password,
            account=settings.snowflake_account,
            warehouse=settings.snowflake_warehouse,
            database=settings.snowflake_database,
            schema=settings.snowflake_schema,
            role=settings.snowflake_role
        )
    
    async def get_available_data(self) -> Dict[str, Any]:
        """Get metadata about available data in Snowflake"""
        if not self.use_snowflake:
            return {
                "tables": [],
                "companies": [],
                "columns": [],
                "error": "Snowflake not configured"
            }
        
        try:
            conn = self.get_snowflake_connection()
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute(f"SHOW TABLES IN {settings.snowflake_database}.{settings.snowflake_schema}")
            tables = [row[1] for row in cursor.fetchall()]
            
            # Get actual columns from the table
            columns = []
            if "EXTRACTED_METRICS" in tables:
                cursor.execute(f"DESCRIBE TABLE {settings.snowflake_database}.{settings.snowflake_schema}.EXTRACTED_METRICS")
                columns = [row[0] for row in cursor.fetchall()]
            
            # Get company names
            companies = []
            if "EXTRACTED_METRICS" in tables and "COMPANY_NAME" in columns:
                cursor.execute("SELECT DISTINCT COMPANY_NAME FROM EXTRACTED_METRICS WHERE COMPANY_NAME IS NOT NULL")
                companies = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return {
                "tables": tables,
                "companies": companies,
                "columns": columns
            }
        except Exception as e:
            print(f"Error getting metadata: {e}")
            return {
                "tables": [],
                "companies": [],
                "columns": [],
                "error": str(e)
            }
    
    async def execute_snowflake_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results"""
        if not self.use_snowflake:
            return []
        
        try:
            conn = self.get_snowflake_connection()
            cursor = conn.cursor()
            cursor.execute(sql)
            
            columns = [col[0] for col in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            conn.close()
            
            return results
        except Exception as e:
            print(f"Query execution error: {e}")
            raise ValueError(f"Failed to execute query: {str(e)}")
    
    def build_system_prompt(self, metadata: Dict[str, Any]) -> str:
        """Build dynamic system prompt based on available data"""
        
        tables_list = metadata.get('tables', [])
        companies_list = metadata.get('companies', [])
        columns_list = metadata.get('columns', [])
        
        # Build schema information dynamically
        schema_info = f"""
DATABASE: {settings.snowflake_database}
SCHEMA: {settings.snowflake_schema}

AVAILABLE TABLES: {', '.join(tables_list) if tables_list else 'None'}

AVAILABLE COLUMNS IN EXTRACTED_METRICS:
{chr(10).join(f'{i+1}. {col}' for i, col in enumerate(columns_list))}

SAMPLE COMPANIES ({len(companies_list)} total):
{', '.join(companies_list[:20])}{'...' if len(companies_list) > 20 else ''}
"""
        
        # Create example query dynamically based on available columns
        example_query = self._build_example_query(columns_list)
        
        system_prompt = f"""You are a financial data analysis assistant for an investment dashboard. You analyze company financial data and provide actionable insights.

{schema_info}

CORE PRINCIPLES:

1. Data Querying:
   - Use fully qualified table names: {settings.snowflake_database}.{settings.snowflake_schema}.EXTRACTED_METRICS
   - Always filter out null values in key columns
   - Group by company name and aggregate metrics using SUM() to handle multiple records per company
   - Default to showing all companies unless the user specifies a limit or specific companies
   - Order results by the most relevant metric for the query (typically net worth or total assets descending)

2. Query Construction:
   - Only use columns that exist in the schema
   - When calculating derived metrics (like net worth), use arithmetic on aggregated values
   - Include WHERE clauses only when filtering is explicitly needed
   - Use appropriate JOIN operations if querying multiple tables

3. Response Handling for Non-Analytical Queries:
   - For greetings or casual messages: Respond with a friendly greeting and suggest what kind of analysis you can help with
   - For unclear queries: Ask clarifying questions about what specific financial metrics or companies they want to analyze
   - For queries outside your scope: Politely redirect to financial data analysis topics

{example_query}

RESPONSE STRUCTURE:

You must respond with valid JSON containing:

{{
  "sql_query": "Your SQL query here (or null if no query needed)",
  "chart_type": "bar|line|table|null",
  "chart_config": {{
    "title": "Descriptive title for the visualization",
    "x_axis": "Column name for x-axis",
    "y_axis": "Column name or metric for y-axis",
    "series": ["List of metrics to display"]
  }},
  "summary": "A concise 2-3 sentence natural language summary of what the data reveals",
  "insights": [
    "Detailed observation about the data with specific numbers and context",
    "Another insight comparing metrics or highlighting trends",
    "Additional finding with financial ratios or relationships"
  ]
}}

INSIGHT GENERATION RULES:

- Write in natural, professional language as if briefing a financial analyst
- Always include specific numbers, percentages, and calculated ratios in your insights
- Use plain text only (no markdown formatting, no asterisks, no special characters for emphasis)
- Start each insight with a hyphen and space (- )
- Mention every company returned in the query results with their key metrics
- Calculate and reference financial health indicators like asset-to-liability ratios, debt ratios, or relative performance
- Provide context by comparing companies or explaining what the numbers indicate about financial health
- Avoid generic statements; be specific about what the data shows and what it means

VISUALIZATION GUIDELINES:

- Choose chart types based on the query intent:
  * Bar charts for comparing companies on single metrics
  * Grouped bar charts for multi-metric comparisons
  * Line charts for trends over time (if temporal data exists)
  * Tables for detailed breakdowns with many columns
- Always include clear, descriptive titles
- Use the most relevant metric for the y-axis (usually what the user is asking about)
- Ensure chart configuration matches the data being returned

QUALITY STANDARDS:

- Be precise with numbers (use actual values from the data)
- Maintain a professional, analytical tone
- Provide actionable intelligence, not just data summaries
- Consider the business context of financial metrics
- Handle edge cases gracefully (empty results, single company, etc.)

Remember: Your role is to transform raw financial data into clear, actionable insights that help users understand company performance and make informed decisions."""

        return system_prompt
    
    def _build_example_query(self, columns: List[str]) -> str:
        """Build example queries dynamically based on available columns"""
        
        if not columns:
            return ""
        
        # Identify key columns
        has_company = 'COMPANY_NAME' in columns
        has_assets = 'TOTAL_ASSETS' in columns
        has_liabilities = 'TOTAL_LIABILITIES' in columns
        
        examples = "EXAMPLE QUERIES:\n\n"
        
        if has_company and has_assets and has_liabilities:
            examples += f"""
```sql
-- Retrieve all companies with aggregated financial data
SELECT
    COMPANY_NAME,
    SUM(TOTAL_ASSETS) as TOTAL_ASSETS,
    SUM(TOTAL_LIABILITIES) as TOTAL_LIABILITIES,
    SUM(TOTAL_ASSETS) - SUM(TOTAL_LIABILITIES) as NET_WORTH
FROM {settings.snowflake_database}.{settings.snowflake_schema}.EXTRACTED_METRICS
WHERE COMPANY_NAME IS NOT NULL
GROUP BY COMPANY_NAME
ORDER BY NET_WORTH DESC;
```

```sql
-- Compare specific companies
SELECT
    COMPANY_NAME,
    SUM(TOTAL_ASSETS) as TOTAL_ASSETS,
    SUM(TOTAL_LIABILITIES) as TOTAL_LIABILITIES
FROM {settings.snowflake_database}.{settings.snowflake_schema}.EXTRACTED_METRICS
WHERE COMPANY_NAME IN ('Company A', 'Company B')
GROUP BY COMPANY_NAME;
```
"""
        elif has_company:
            examples += f"""
```sql
-- Retrieve available company data
SELECT
    COMPANY_NAME,
    {', '.join(f'SUM({col}) as {col}' if col != 'COMPANY_NAME' else col for col in columns[:5])}
FROM {settings.snowflake_database}.{settings.snowflake_schema}.EXTRACTED_METRICS
WHERE COMPANY_NAME IS NOT NULL
GROUP BY COMPANY_NAME
ORDER BY COMPANY_NAME;
```
"""
        
        return examples
    
    async def analyze_query(
        self, 
        user_query: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Main analysis method - interprets query and generates response"""
        
        if not self.use_gemini:
            return {
                "summary": "AI analysis not available - Gemini API key not configured",
                "insights": [],
                "error": "Gemini API not configured"
            }
        
        # Throttle requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        
        # Get available data context
        metadata = await self.get_available_data()
        
        # Build dynamic system prompt
        system_prompt = self.build_system_prompt(metadata)
        
        # Build conversation context
        context = ""
        if conversation_history:
            context = "\n\nConversation History:\n"
            for msg in conversation_history[-5:]:
                context += f"{msg['role']}: {msg['content']}\n"
        
        # STEP 1: First, get the SQL query from AI
        query_generation_prompt = f"""{system_prompt}

{context}

User Query: {user_query}

First, generate ONLY the SQL query needed to answer this question. Respond with a JSON object containing just the sql_query field:
{{
  "sql_query": "Your SQL query here"
}}"""

        try:
            # Get SQL query first
            max_retries = 3
            query_response = None
            
            for attempt in range(max_retries):
                try:
                    query_response = self.model.generate_content(query_generation_prompt)
                    break
                except ResourceExhausted as e:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 3
                        print(f"⏳ Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        return {
                            "summary": "The AI service is currently experiencing high demand. Please wait a moment and try again.",
                            "insights": ["Rate limit exceeded - please try again in a few seconds"],
                            "error": "Rate limit exceeded",
                            "available_companies": metadata.get('companies', []),
                            "available_columns": metadata.get('columns', [])
                        }
            
            if not query_response:
                raise Exception("Failed to get query response after retries")
            
            query_text = query_response.text.strip()
            
            # Extract JSON from response
            if "```json" in query_text:
                start = query_text.find("```json") + 7
                end = query_text.find("```", start)
                query_text = query_text[start:end]
            elif "```" in query_text:
                start = query_text.find("```") + 3
                end = query_text.find("```", start)
                query_text = query_text[start:end]
            
            query_data = json.loads(query_text.strip())
            
            # STEP 2: Execute SQL query
            query_results = []
            if query_data.get("sql_query"):
                try:
                    query_results = await self.execute_snowflake_query(query_data["sql_query"])
                except Exception as e:
                    return {
                        "summary": f"Unable to retrieve data: {str(e)}",
                        "insights": ["Please verify the query parameters or check data availability"],
                        "error": str(e),
                        "available_companies": metadata.get('companies', []),
                        "available_columns": metadata.get('columns', [])
                    }
            
            # STEP 3: Now generate insights with actual data
            analysis_prompt = f"""{system_prompt}

{context}

User Query: {user_query}

SQL Query Executed:
{query_data.get("sql_query")}

QUERY RESULTS (ACTUAL DATA):
{json.dumps(query_results, indent=2, default=str)}

Now generate a complete analysis response using the ACTUAL DATA above. Your insights MUST include the specific numbers from the query results. Never use placeholders like [replace with actual value]. Use the real values you see in the query results.

Respond with a JSON object:
{{
  "sql_query": "the query that was executed",
  "chart_type": "bar|line|table|null",
  "chart_config": {{...}},
  "summary": "Natural language summary using actual numbers from results",
  "insights": [
    "Insight with specific numbers from the data",
    "Another insight with calculations and real values"
  ]
}}"""

            # Get final analysis with actual data
            analysis_response = None
            for attempt in range(max_retries):
                try:
                    analysis_response = self.model.generate_content(analysis_prompt)
                    break
                except ResourceExhausted as e:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 3
                        time.sleep(wait_time)
                    else:
                        return {
                            "summary": "The AI service is currently experiencing high demand. Please wait a moment and try again.",
                            "insights": ["Rate limit exceeded - please try again in a few seconds"],
                            "error": "Rate limit exceeded"
                        }
            
            if not analysis_response:
                raise Exception("Failed to get analysis after retries")
            
            response_text = analysis_response.text.strip()
            
            # Extract JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end]
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end]
            
            analysis = json.loads(response_text.strip())
            
            # Build chart data
            chart = None
            if analysis.get("chart_type") and query_results:
                chart = {
                    "chart_type": analysis["chart_type"],
                    "title": analysis.get("chart_config", {}).get("title", "Analysis Results"),
                    "x_axis": analysis.get("chart_config", {}).get("x_axis", ""),
                    "y_axis": analysis.get("chart_config", {}).get("y_axis", ""),
                    "series": analysis.get("chart_config", {}).get("series", []),
                    "data": query_results
                }
            
            return {
                "summary": analysis.get("summary", "Analysis complete"),
                "insights": analysis.get("insights", []),
                "chart": chart,
                "available_companies": metadata.get('companies', []),
                "available_columns": metadata.get('columns', [])
            }
            
        except Exception as e:
            print(f"Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "summary": "An error occurred while processing your request. Please try rephrasing your query or contact support if the issue persists.",
                "insights": [f"Error details: {str(e)}"],
                "error": str(e),
                "available_companies": metadata.get('companies', []),
                "available_columns": metadata.get('columns', [])
            }