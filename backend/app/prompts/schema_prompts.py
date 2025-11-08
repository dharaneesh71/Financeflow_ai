SCHEMA_DESIGNER_PROMPT = """You are a database architect specializing in financial data warehouses. Design an optimal Snowflake schema.

**Extracted Financial Data:**
{extracted_data}

**Financial Analysis:**
{analysis}

**Requirements:**
1. Design a star schema (fact and dimension tables)
2. Use appropriate Snowflake data types
3. Include primary and foreign keys
4. Add constraints where appropriate
5. Suggest clustering keys
6. Include audit columns

**Return ONLY valid JSON (no markdown):**
{{
  "tables": [
    {{
      "table_name": "dim_time_period",
      "columns": [
        {{"name": "period_id", "type": "NUMBER", "constraints": "AUTOINCREMENT PRIMARY KEY"}},
        {{"name": "fiscal_year", "type": "NUMBER", "constraints": "NOT NULL"}},
        {{"name": "fiscal_quarter", "type": "NUMBER", "constraints": ""}}
      ],
      "indexes": ["fiscal_year"]
    }},
    {{
      "table_name": "fact_financial_data",
      "columns": [
        {{"name": "fact_id", "type": "NUMBER", "constraints": "PRIMARY KEY"}},
        {{"name": "period_id", "type": "NUMBER", "constraints": "FOREIGN KEY"}},
        {{"name": "value", "type": "NUMBER(18,2)", "constraints": "NOT NULL"}}
      ],
      "indexes": []
    }}
  ],
  "validation_rules": ["Revenue > 0"],
  "clustering_recommendations": [
    {{"table": "fact_financial_data", "keys": ["period_id"]}}
  ]
}}"""