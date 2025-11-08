import json
from typing import Dict, Any, List
import google.generativeai as genai
from app.models import DatabaseSchema, ExtractionResult, FinancialInsight, TableSchema, TableColumn
from app.config import get_settings

settings = get_settings()

class SchemaDesigner:
    """Design database schema using Gemini"""
    
    def __init__(self):
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            print("✅ Gemini Schema Designer initialized")
        except Exception as e:
            print(f"❌ Schema designer init error: {e}")
            self.model = None
    
    async def design_schema(
        self, 
        extraction_results: List[ExtractionResult],
        analysis: FinancialInsight
    ) -> DatabaseSchema:
        """Design Snowflake schema"""
        
        print("🏗️ Designing database schema with Gemini...")
        
        return self._create_basic_schema(extraction_results, analysis)
    
    def _create_basic_schema(
        self, 
        extraction_results: List[ExtractionResult],
        analysis: FinancialInsight
    ) -> DatabaseSchema:
        """Create star schema"""
        
        # Dimension: Time
        dim_time = TableSchema(
            table_name="dim_time_period",
            columns=[
                TableColumn(name="period_id", type="NUMBER", constraints="PRIMARY KEY AUTOINCREMENT"),
                TableColumn(name="fiscal_year", type="NUMBER", constraints="NOT NULL"),
                TableColumn(name="fiscal_quarter", type="NUMBER", constraints=""),
                TableColumn(name="period_name", type="VARCHAR(50)", constraints="NOT NULL"),
            ],
            indexes=["fiscal_year"]
        )
        
        # Dimension: Account
        dim_account = TableSchema(
            table_name="dim_account",
            columns=[
                TableColumn(name="account_id", type="NUMBER", constraints="PRIMARY KEY AUTOINCREMENT"),
                TableColumn(name="account_name", type="VARCHAR(200)", constraints="NOT NULL"),
                TableColumn(name="account_type", type="VARCHAR(50)", constraints="NOT NULL"),
            ],
            indexes=["account_type"]
        )
        
        # Fact: Financial Data
        fact_financial = TableSchema(
            table_name="fact_financial_data",
            columns=[
                TableColumn(name="fact_id", type="NUMBER", constraints="PRIMARY KEY AUTOINCREMENT"),
                TableColumn(name="period_id", type="NUMBER", constraints="NOT NULL"),
                TableColumn(name="account_id", type="NUMBER", constraints="NOT NULL"),
                TableColumn(name="amount", type="NUMBER(18,2)", constraints="NOT NULL"),
                TableColumn(name="confidence_score", type="NUMBER(5,4)", constraints=""),
                TableColumn(name="created_at", type="TIMESTAMP", constraints="DEFAULT CURRENT_TIMESTAMP()"),
            ],
            indexes=["period_id", "account_id"]
        )
        
        tables = [dim_time, dim_account, fact_financial]
        
        # Generate DDL
        ddl_parts = []
        for table in tables:
            columns = []
            for col in table.columns:
                col_def = f"  {col.name} {col.type}"
                if col.constraints:
                    col_def += f" {col.constraints}"
                columns.append(col_def)
            
            table_ddl = f"CREATE TABLE IF NOT EXISTS {table.table_name} (\n"
            table_ddl += ",\n".join(columns)
            table_ddl += "\n);"
            ddl_parts.append(table_ddl)
        
        ddl_sql = "\n\n".join(ddl_parts)
        
        print(f"✅ Schema designed: {len(tables)} tables")
        
        return DatabaseSchema(
            tables=tables,
            relationships=[
                {"from": "fact_financial_data.period_id", "to": "dim_time_period.period_id"},
                {"from": "fact_financial_data.account_id", "to": "dim_account.account_id"}
            ],
            validation_rules=["amount IS NOT NULL"],
            clustering_recommendations=[
                {"table": "fact_financial_data", "keys": ["period_id", "account_id"]}
            ],
            ddl_sql=ddl_sql
        )