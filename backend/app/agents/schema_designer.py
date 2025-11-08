import json
from typing import Dict, Any, List
import google.generativeai as genai
from app.models import DatabaseSchema, ExtractionResult, FinancialInsight, TableSchema, TableColumn
from app.config import get_settings

settings = get_settings()

class SchemaDesigner:
    """Design optimal database schema using Gemini AI"""
    
    def __init__(self):
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.use_gemini = True
            print("✅ Gemini Schema Designer initialized")
        except Exception as e:
            print(f"⚠️  Schema designer initialization error: {e}")
            self.use_gemini = False
    
    async def design_schema(
        self, 
        extraction_results: List[ExtractionResult],
        analysis: FinancialInsight
    ) -> DatabaseSchema:
        """Design optimal Snowflake database schema"""
        
        # For now, always use basic schema (Gemini schema generation can be added later)
        return self._create_star_schema(extraction_results, analysis)
    
    def _create_star_schema(
        self, 
        extraction_results: List[ExtractionResult],
        analysis: FinancialInsight
    ) -> DatabaseSchema:
        """Create a star schema for financial data"""
        
        print("  🏗️  Creating star schema...")
        
        # DIMENSION TABLE: Time Period
        dim_time = TableSchema(
            table_name="DIM_TIME_PERIOD",
            columns=[
                TableColumn(name="PERIOD_ID", type="NUMBER", constraints="PRIMARY KEY AUTOINCREMENT"),
                TableColumn(name="FISCAL_YEAR", type="NUMBER", constraints="NOT NULL"),
                TableColumn(name="FISCAL_QUARTER", type="NUMBER", constraints=""),
                TableColumn(name="PERIOD_NAME", type="VARCHAR(50)", constraints="NOT NULL"),
                TableColumn(name="PERIOD_TYPE", type="VARCHAR(20)", constraints=""),
                TableColumn(name="CREATED_AT", type="TIMESTAMP", constraints="DEFAULT CURRENT_TIMESTAMP()"),
            ],
            indexes=["FISCAL_YEAR", "FISCAL_QUARTER"]
        )
        
        # DIMENSION TABLE: Account/Line Item
        dim_account = TableSchema(
            table_name="DIM_ACCOUNT",
            columns=[
                TableColumn(name="ACCOUNT_ID", type="NUMBER", constraints="PRIMARY KEY AUTOINCREMENT"),
                TableColumn(name="ACCOUNT_NAME", type="VARCHAR(200)", constraints="NOT NULL"),
                TableColumn(name="ACCOUNT_TYPE", type="VARCHAR(50)", constraints="NOT NULL"),
                TableColumn(name="DOCUMENT_TYPE", type="VARCHAR(50)", constraints=""),
                TableColumn(name="PARENT_ACCOUNT", type="VARCHAR(200)", constraints=""),
                TableColumn(name="CREATED_AT", type="TIMESTAMP", constraints="DEFAULT CURRENT_TIMESTAMP()"),
            ],
            indexes=["ACCOUNT_TYPE", "DOCUMENT_TYPE"]
        )
        
        # DIMENSION TABLE: Document Source
        dim_document = TableSchema(
            table_name="DIM_DOCUMENT",
            columns=[
                TableColumn(name="DOCUMENT_ID", type="NUMBER", constraints="PRIMARY KEY AUTOINCREMENT"),
                TableColumn(name="FILE_NAME", type="VARCHAR(255)", constraints="NOT NULL"),
                TableColumn(name="DOCUMENT_TYPE", type="VARCHAR(50)", constraints=""),
                TableColumn(name="UPLOAD_DATE", type="TIMESTAMP", constraints="DEFAULT CURRENT_TIMESTAMP()"),
                TableColumn(name="PROCESSING_STATUS", type="VARCHAR(20)", constraints=""),
            ],
            indexes=["DOCUMENT_TYPE", "UPLOAD_DATE"]
        )
        
        # FACT TABLE: Financial Data
        fact_financial = TableSchema(
            table_name="FACT_FINANCIAL_DATA",
            columns=[
                TableColumn(name="FACT_ID", type="NUMBER", constraints="PRIMARY KEY AUTOINCREMENT"),
                TableColumn(name="PERIOD_ID", type="NUMBER", constraints="NOT NULL"),
                TableColumn(name="ACCOUNT_ID", type="NUMBER", constraints="NOT NULL"),
                TableColumn(name="DOCUMENT_ID", type="NUMBER", constraints=""),
                TableColumn(name="AMOUNT", type="NUMBER(18,2)", constraints="NOT NULL"),
                TableColumn(name="CONFIDENCE_SCORE", type="NUMBER(5,4)", constraints=""),
                TableColumn(name="DATA_TYPE", type="VARCHAR(50)", constraints=""),
                TableColumn(name="CURRENCY", type="VARCHAR(10)", constraints="DEFAULT 'USD'"),
                TableColumn(name="CREATED_AT", type="TIMESTAMP", constraints="DEFAULT CURRENT_TIMESTAMP()"),
                TableColumn(name="UPDATED_AT", type="TIMESTAMP", constraints="DEFAULT CURRENT_TIMESTAMP()"),
            ],
            indexes=["PERIOD_ID", "ACCOUNT_ID", "DOCUMENT_ID"]
        )
        
        tables = [dim_time, dim_account, dim_document, fact_financial]
        
        # Generate DDL SQL
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
        
        # Add clustering recommendations
        ddl_parts.append("\n-- Clustering")
        ddl_parts.append("ALTER TABLE FACT_FINANCIAL_DATA CLUSTER BY (PERIOD_ID, ACCOUNT_ID);")
        
        ddl_sql = "\n\n".join(ddl_parts)
        
        print(f"  ✅ Schema created: {len(tables)} tables")
        
        return DatabaseSchema(
            tables=tables,
            relationships=[
                {"from": "FACT_FINANCIAL_DATA.PERIOD_ID", "to": "DIM_TIME_PERIOD.PERIOD_ID"},
                {"from": "FACT_FINANCIAL_DATA.ACCOUNT_ID", "to": "DIM_ACCOUNT.ACCOUNT_ID"},
                {"from": "FACT_FINANCIAL_DATA.DOCUMENT_ID", "to": "DIM_DOCUMENT.DOCUMENT_ID"}
            ],
            validation_rules=[
                "AMOUNT IS NOT NULL",
                "CONFIDENCE_SCORE BETWEEN 0 AND 1",
                "PERIOD_ID > 0",
                "ACCOUNT_ID > 0"
            ],
            clustering_recommendations=[
                {
                    "table": "FACT_FINANCIAL_DATA",
                    "keys": ["PERIOD_ID", "ACCOUNT_ID"],
                    "reason": "Optimize for time-series and account-based queries"
                }
            ],
            ddl_sql=ddl_sql
        )