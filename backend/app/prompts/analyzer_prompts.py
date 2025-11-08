FINANCIAL_ANALYZER_PROMPT = """You are a financial analysis expert. Analyze the following extracted financial data.

**Extracted Data:**
{extracted_data}

**Your Task:**
1. Identify the document type (P&L, Balance Sheet, Cash Flow)
2. Detect the time period (quarterly, annual, fiscal year)
3. Find relationships between metrics (e.g., Revenue - COGS = Gross Profit)
4. Identify calculated vs. reported fields
5. Suggest additional useful metrics
6. Assess data quality
7. Flag anomalies or missing information

**Return ONLY valid JSON (no markdown):**
{{
  "document_type": "income_statement",
  "time_period": "quarterly",
  "fiscal_year": 2024,
  "fiscal_quarter": 3,
  "detected_relationships": [
    {{
      "type": "calculation",
      "formula": "Gross Profit = Revenue - COGS",
      "components_present": true
    }}
  ],
  "suggested_metrics": ["Gross Profit Margin %", "Operating Margin %"],
  "data_quality": {{
    "completeness": 0.95,
    "consistency_score": 0.92
  }},
  "issues": ["Missing depreciation detail"],
  "insights": ["Revenue is strong for Q3"]
}}"""