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
                "metrics": [],
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
                cursor.execute("SELECT DISTINCT COMPANY_NAME FROM EXTRACTED_METRICS WHERE COMPANY_NAME IS NOT NULL LIMIT 100")
                companies = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return {
                "tables": tables,
                "companies": companies,
                "metrics": columns,
                "columns": columns
            }
        except Exception as e:
            print(f"Error getting metadata: {e}")
            import traceback
            traceback.print_exc()
            return {
                "tables": [],
                "companies": [],
                "metrics": [],
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
        
        schema_info = f"""
DATABASE: {settings.snowflake_database}
SCHEMA: {settings.snowflake_schema}

AVAILABLE TABLES: {', '.join(tables_list) if tables_list else 'None'}

AVAILABLE COLUMNS IN EXTRACTED_METRICS:
{chr(10).join(f'  - {col}' for col in columns_list)}

AVAILABLE COMPANIES ({len(companies_list)} total):
{', '.join(companies_list)}
"""
        
        system_prompt = f"""You are an AI financial analyst assistant. Your job is to understand user requests, generate appropriate SQL queries, and provide insights.

{schema_info}

CORE RESPONSIBILITIES:

1. UNDERSTAND THE USER'S REQUEST
   - Identify what data they want to see
   - Determine the presentation format they prefer (table, chart, or analysis)
   - Detect if the requested data exists in the schema

2. SQL QUERY GENERATION RULES
   - NEVER nest aggregate functions (SUM(SUM(...)) is INVALID)
   - Always use fully qualified table names: {settings.snowflake_database}.{settings.snowflake_schema}.EXTRACTED_METRICS
   - When using aggregate functions, include GROUP BY clause
   - Only use columns that exist in the schema above
   - Filter NULL values: WHERE COMPANY_NAME IS NOT NULL

3. VISUALIZATION SELECTION (Based on user request)
   - If user asks for "table" or "in table format" → use "table" chart_type
   - If user asks for "chart", "graph", "visualize", "compare visually" → use "bar" or "line" chart_type
   - If user asks for "analysis" or "insights" only → use null chart_type
   - DEFAULT: If unclear, use "table" for data with multiple columns, "bar" for comparisons

4. HANDLING DIFFERENT SCENARIOS

   A. Data exists and query is valid:
      - Generate proper SQL query
      - Choose appropriate visualization based on user request
      - Set chart_type correctly

   B. Data doesn't exist:
      - Set sql_query to null
      - Politely inform user that the requested data is not available
      - List what data IS available

   C. User asks for impossible operations:
      - Set sql_query to null
      - Clearly explain why it's not possible
      - Suggest alternatives if any

   D. Greeting or casual conversation:
      - Set sql_query to null
      - Respond naturally and ask how you can help

CORRECT SQL EXAMPLES:

```sql
-- Get all companies with financial metrics
SELECT 
    COMPANY_NAME,
    SUM(TOTAL_ASSETS) as TOTAL_ASSETS,
    SUM(TOTAL_LIABILITIES) as TOTAL_LIABILITIES,
    SUM(TOTAL_EQUITY) as TOTAL_EQUITY
FROM {settings.snowflake_database}.{settings.snowflake_schema}.EXTRACTED_METRICS
WHERE COMPANY_NAME IS NOT NULL
GROUP BY COMPANY_NAME
ORDER BY TOTAL_ASSETS DESC;
```

```sql
-- Compare specific companies
SELECT 
    COMPANY_NAME,
    SUM(TOTAL_ASSETS) as TOTAL_ASSETS,
    SUM(TOTAL_LIABILITIES) as TOTAL_LIABILITIES
FROM {settings.snowflake_database}.{settings.snowflake_schema}.EXTRACTED_METRICS
WHERE COMPANY_NAME IN ('Microsoft', 'Apple Inc.')
GROUP BY COMPANY_NAME;
```

RESPONSE FORMAT (JSON):

{{
  "sql_query": "Valid SQL query OR null if no query needed",
  "chart_type": "table|bar|line|null (MUST match user's request format)",
  "chart_config": {{
    "title": "Clear, descriptive title",
    "x_axis": "Column for x-axis (usually COMPANY_NAME)",
    "y_axis": "Metric name",
    "series": ["List of metrics to display"]
  }} OR null,
  "requires_followup": false,
  "followup_message": null
}}

IMPORTANT RULES:
- If user says "table", "in table", "show me in table" → ALWAYS use chart_type: "table"
- If user says "chart", "graph", "visualize" → use chart_type: "bar" or "line"
- If data doesn't exist → sql_query: null, and explain what's missing
- If operation is impossible → sql_query: null, and explain why
- Never include summary or insights in this initial response - they will be generated later based on actual data
- Be precise about chart_type selection based on user's explicit request"""

        return system_prompt
    
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
        
        # STEP 1: Understand query and generate SQL
        query_prompt = f"""{system_prompt}

{context}

User Query: "{user_query}"

Analyze this query carefully:
1. What data is the user asking for?
2. Does this data exist in the schema?
3. What format do they want (table, chart, or just insights)?
4. Is this request possible with the available data?

Respond with JSON containing sql_query and chart_type selection."""

        try:
            max_retries = 3
            response = None
            
            # Get response from AI
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(query_prompt)
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
                            "available_metrics": metadata.get('metrics', [])
                        }
            
            if not response:
                raise Exception("Failed to get response after retries")
            
            response_text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end]
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end]
            
            analysis = json.loads(response_text.strip())
            
            # Check if this requires a followup (data doesn't exist, impossible request, etc.)
            if analysis.get("requires_followup") or not analysis.get("sql_query"):
                if analysis.get("followup_message"):
                    return {
                        "summary": analysis["followup_message"],
                        "insights": [],
                        "available_companies": metadata.get('companies', []),
                        "available_metrics": metadata.get('metrics', [])
                    }
                # This is a greeting or general question
                return {
                    "summary": "Hi! I can help you analyze financial data. What would you like to know?",
                    "insights": [
                        f"Available companies: {', '.join(metadata.get('companies', []))}",
                        f"Available metrics: {', '.join(metadata.get('metrics', [])[:5])}..."
                    ],
                    "available_companies": metadata.get('companies', []),
                    "available_metrics": metadata.get('metrics', [])
                }
            
            # STEP 2: Execute SQL query
            sql_query = analysis.get("sql_query")
            print(f"🔍 GENERATED SQL:\n{sql_query}")
            
            query_results = []
            try:
                query_results = await self.execute_snowflake_query(sql_query)
                print(f"✅ Query returned {len(query_results)} rows")
            except Exception as e:
                sql_error = str(e)
                print(f"❌ SQL execution error: {sql_error}")
                
                return {
                    "summary": "I encountered an error while querying the database. Let me help you rephrase your request.",
                    "insights": [
                        "The query couldn't be executed. This might be due to:",
                        "- Invalid column names or table structure",
                        "- Syntax error in the generated query",
                        f"- Technical error: {sql_error[:100]}",
                        "",
                        "Please try rephrasing your question or ask about:",
                        f"- {', '.join(metadata.get('companies', [])[:3])}",
                        f"- Metrics like: {', '.join(metadata.get('metrics', [])[:3])}"
                    ],
                    "available_companies": metadata.get('companies', []),
                    "available_metrics": metadata.get('metrics', [])
                }
            
            # STEP 3: Check if we got results
            if not query_results or len(query_results) == 0:
                return {
                    "summary": "Sorry, I couldn't find any data matching your request in the database.",
                    "insights": [
                        "The query executed successfully but returned no results.",
                        "This could mean:",
                        "- The data you're looking for doesn't exist",
                        "- The filters were too specific",
                        "",
                        "Available data in the database:",
                        f"- Companies: {', '.join(metadata.get('companies', []))}",
                        f"- Metrics: {', '.join(metadata.get('metrics', []))}"
                    ],
                    "available_companies": metadata.get('companies', []),
                    "available_metrics": metadata.get('metrics', [])
                }
            
            # STEP 4: Generate dynamic insights based on actual data
            chart_info = ""
            if analysis.get("chart_type"):
                if analysis["chart_type"] == "bar":
                    chart_info = "\n\nIMPORTANT: A bar chart visualization has been created. You MUST reference it in your summary (e.g., 'As shown in the bar chart above...')."
                elif analysis["chart_type"] == "line":
                    chart_info = "\n\nIMPORTANT: A line chart has been created. You MUST reference it in your summary."
                elif analysis["chart_type"] == "table":
                    chart_info = "\n\nIMPORTANT: The data is displayed in a table format. You MUST reference it."
            
            insights_prompt = f"""You are a financial analyst AI. Analyze the data below and provide a professional financial comparison.

User Query: "{user_query}"

ACTUAL QUERY RESULTS:
{json.dumps(query_results, indent=2, default=str)}
{chart_info}

TASK:
Write a professional financial analysis comparing these companies. Be specific, use actual numbers, and provide meaningful insights.

RESPONSE FORMAT - YOU MUST RESPOND WITH VALID JSON ONLY:
{{
  "summary": "2-3 sentence summary with specific numbers and chart reference if applicable",
  "insights": [
    "First insight comparing specific metrics with actual values",
    "Second insight about financial ratios or performance",
    "Third insight highlighting key differences or patterns",
    "Fourth insight with calculations or percentages"
  ]
}}

CRITICAL RULES:
1. Use ONLY the actual numbers from the data above
2. Calculate ratios, percentages, and comparisons
3. If a chart exists, naturally mention it (e.g., "The chart illustrates...")
4. Make each insight meaningful and specific
5. Start each insight with "- "
6. Compare companies directly with numbers

EXAMPLE GOOD INSIGHT:
"- Apple Inc. has higher liabilities ($308,030) compared to its equity ($56,950), indicating a debt-heavy capital structure with a debt-to-equity ratio of 5.4x."

RESPOND WITH JSON ONLY - NO OTHER TEXT:"""

            # Get AI-generated insights
            insights_response = None
            for attempt in range(max_retries):
                try:
                    print(f"🤖 Requesting insights from AI (attempt {attempt + 1})...")
                    insights_response = self.model.generate_content(insights_prompt)
                    print(f"✅ Got insights response")
                    break
                except ResourceExhausted:
                    if attempt < max_retries - 1:
                        time.sleep((2 ** attempt) * 3)
                    else:
                        print("❌ Rate limit exceeded while generating insights")
            
            if insights_response:
                insights_text = insights_response.text.strip()
                print(f"📝 Raw insights response length: {len(insights_text)}")
                print(f"📝 First 200 chars: {insights_text[:200]}")
                
                # Extract JSON
                if "```json" in insights_text:
                    start = insights_text.find("```json") + 7
                    end = insights_text.find("```", start)
                    insights_text = insights_text[start:end]
                elif "```" in insights_text:
                    start = insights_text.find("```") + 3
                    end = insights_text.find("```", start)
                    insights_text = insights_text[start:end]
                
                try:
                    insights_data = json.loads(insights_text.strip())
                    summary = insights_data.get("summary", "")
                    insights = insights_data.get("insights", [])
                    
                    # Validate that we got meaningful content
                    if not summary or len(summary) < 20:
                        raise ValueError("Summary too short or empty")
                    if not insights or len(insights) == 0:
                        raise ValueError("No insights generated")
                    
                    print(f"✅ Successfully parsed insights - Summary length: {len(summary)}, Insights count: {len(insights)}")
                        
                except Exception as parse_error:
                    print(f"❌ Failed to parse insights JSON: {parse_error}")
                    print(f"📄 Raw insights text: {insights_text[:500]}")
                    
                    # Generate fallback insights with actual analysis
                    summary = "Here's a detailed financial comparison based on the data:"
                    insights = []
                    
                    # Analyze the data and create meaningful insights
                    if len(query_results) >= 2:
                        # Compare first two companies
                        comp1 = query_results[0]
                        comp2 = query_results[1]
                        
                        name1 = comp1.get('COMPANY_NAME', 'Company 1')
                        name2 = comp2.get('COMPANY_NAME', 'Company 2')
                        
                        assets1 = comp1.get('TOTAL_ASSETS', 0)
                        assets2 = comp2.get('TOTAL_ASSETS', 0)
                        liab1 = comp1.get('TOTAL_LIABILITIES', 0)
                        liab2 = comp2.get('TOTAL_LIABILITIES', 0)
                        equity1 = comp1.get('TOTAL_EQUITY', 0)
                        equity2 = comp2.get('TOTAL_EQUITY', 0)
                        
                        # Compare assets
                        if assets1 > assets2:
                            diff_pct = ((assets1 - assets2) / assets2 * 100) if assets2 > 0 else 0
                            insights.append(f"- {name1} has significantly higher total assets (${assets1:,.2f}) compared to {name2} (${assets2:,.2f}), representing a {diff_pct:.1f}% difference.")
                        else:
                            diff_pct = ((assets2 - assets1) / assets1 * 100) if assets1 > 0 else 0
                            insights.append(f"- {name2} has significantly higher total assets (${assets2:,.2f}) compared to {name1} (${assets1:,.2f}), representing a {diff_pct:.1f}% difference.")
                        
                        # Debt-to-equity ratios
                        if equity1 > 0:
                            ratio1 = liab1 / equity1
                            insights.append(f"- {name1} has a debt-to-equity ratio of {ratio1:.2f}x, indicating {'high leverage' if ratio1 > 2 else 'moderate leverage' if ratio1 > 1 else 'conservative capital structure'}.")
                        
                        if equity2 > 0:
                            ratio2 = liab2 / equity2
                            insights.append(f"- {name2} has a debt-to-equity ratio of {ratio2:.2f}x, indicating {'high leverage' if ratio2 > 2 else 'moderate leverage' if ratio2 > 1 else 'conservative capital structure'}.")
                        
                        # Compare equity positions
                        if equity1 > equity2:
                            insights.append(f"- {name1} has a stronger equity position (${equity1:,.2f}) compared to {name2} (${equity2:,.2f}), suggesting better financial stability.")
                        else:
                            insights.append(f"- {name2} has a stronger equity position (${equity2:,.2f}) compared to {name1} (${equity1:,.2f}), suggesting better financial stability.")
                    else:
                        # Single company analysis
                        for row in query_results[:3]:
                            company = row.get('COMPANY_NAME', 'Unknown')
                            assets = row.get('TOTAL_ASSETS', 0)
                            liabilities = row.get('TOTAL_LIABILITIES', 0)
                            equity = row.get('TOTAL_EQUITY', 0)
                            
                            insights.append(f"- {company}: Total Assets ${assets:,.2f}, Liabilities ${liabilities:,.2f}, Equity ${equity:,.2f}")
                            
                            if equity > 0:
                                de_ratio = liabilities / equity
                                insights.append(f"- {company} has a debt-to-equity ratio of {de_ratio:.2f}x")
                    
                    summary = f"Analyzing {len(query_results)} companies. {insights[0] if insights else ''}"
            else:
                print("No insights response from AI")
                summary = f"Retrieved {len(query_results)} companies from the database."
                insights = []
                # Generate basic insights from the data
                for idx, row in enumerate(query_results[:3]):
                    company = row.get('COMPANY_NAME', f'Company {idx+1}')
                    assets = row.get('TOTAL_ASSETS', 0)
                    liabilities = row.get('TOTAL_LIABILITIES', 0)
                    equity = row.get('TOTAL_EQUITY', 0)
                    insights.append(f"- {company}: Assets ${assets:,.2f}, Liabilities ${liabilities:,.2f}, Equity ${equity:,.2f}")
            
                            # Build chart data based on chart_type from analysis
            chart = None
            if analysis.get("chart_type") and analysis.get("chart_type") != "null":
                # Ensure we have proper defaults
                x_axis_key = analysis.get("chart_config", {}).get("x_axis", "COMPANY_NAME")
                series_list = analysis.get("chart_config", {}).get("series", [])
                
                # If no series specified, try to auto-detect numeric columns
                if not series_list and query_results and len(query_results) > 0:
                    first_row = query_results[0]
                    series_list = [k for k, v in first_row.items() 
                                 if k != x_axis_key and isinstance(v, (int, float))]
                
                chart = {
                    "chart_type": analysis["chart_type"],
                    "title": analysis.get("chart_config", {}).get("title", "Financial Analysis"),
                    "x_axis": x_axis_key,
                    "y_axis": analysis.get("chart_config", {}).get("y_axis", series_list[0] if series_list else "value"),
                    "series": series_list,
                    "data": query_results
                }
                
                print(f"📊 Chart config: {chart['chart_type']}, x={chart['x_axis']}, series={chart['series']}")
            
            print(f"📊 Final summary: {summary[:100]}...")
            print(f"📊 Number of insights: {len(insights)}")
            
            return {
                "summary": summary,
                "insights": insights,
                "chart": chart,
                "data": query_results,
                "available_companies": metadata.get('companies', []),
                "available_metrics": metadata.get('metrics', [])
            }
            
        except Exception as e:
            print(f"Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "summary": "I encountered an unexpected error while processing your request.",
                "insights": [
                    "Something went wrong during analysis.",
                    "Please try:",
                    "- Rephrasing your question",
                    "- Asking about specific companies or metrics",
                    "- Checking if the data you're looking for exists",
                    "",
                    f"Error details: {str(e)[:200]}"
                ],
                "error": str(e),
                "available_companies": metadata.get('companies', []),
                "available_metrics": metadata.get('metrics', [])
            }