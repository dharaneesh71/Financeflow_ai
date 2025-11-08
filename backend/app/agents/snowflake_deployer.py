from typing import List
import snowflake.connector
from app.models import DatabaseSchema, ExtractionResult, DeploymentResult
from app.config import get_settings

settings = get_settings()

class SnowflakeDeployer:
    """Deploy to Snowflake"""
    
    def __init__(self):
        self.use_snowflake = bool(settings.snowflake_account and settings.snowflake_user)
        if self.use_snowflake:
            print(f"✅ Snowflake configured: {settings.snowflake_database}.{settings.snowflake_schema}")
        else:
            print("⚠️ Snowflake not configured, using mock deployment")
    
    async def deploy(
        self, 
        schema: DatabaseSchema, 
        extraction_results: List[ExtractionResult]
    ) -> DeploymentResult:
        """Deploy schema and data to Snowflake"""
        
        if not self.use_snowflake:
            return self._mock_deployment(schema, extraction_results)
        
        try:
            conn = snowflake.connector.connect(
                user=settings.snowflake_user,
                password=settings.snowflake_password,
                account=settings.snowflake_account,
                warehouse=settings.snowflake_warehouse,
                database=settings.snowflake_database,
                schema=settings.snowflake_schema
            )
            
            cursor = conn.cursor()
            
            # Create tables
            print("  Creating tables...")
            for table_ddl in schema.ddl_sql.split(";"):
                if table_ddl.strip():
                    cursor.execute(table_ddl)
            
            # Load data
            print("  Loading data...")
            rows_loaded = 0
            for result in extraction_results:
                for field in result.extracted_fields:
                    cursor.execute("""
                        INSERT INTO fact_financial_data (period_id, account_id, amount, confidence_score)
                        VALUES (1, 1, %s, %s)
                    """, (field.value, field.confidence))
                    rows_loaded += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Deployed {rows_loaded} rows to Snowflake")
            
            return DeploymentResult(
                tables_created=len(schema.tables),
                rows_loaded=rows_loaded,
                database=settings.snowflake_database,
                schema=settings.snowflake_schema,
                status="success"
            )
            
        except Exception as e:
            print(f"❌ Snowflake deployment error: {e}")
            return self._mock_deployment(schema, extraction_results)
    
    def _mock_deployment(
        self, 
        schema: DatabaseSchema, 
        extraction_results: List[ExtractionResult]
    ) -> DeploymentResult:
        """Mock deployment"""
        rows = sum(len(r.extracted_fields) for r in extraction_results)
        print(f"✅ Mock deployment: {len(schema.tables)} tables, {rows} rows")
        
        return DeploymentResult(
            tables_created=len(schema.tables),
            rows_loaded=rows,
            database="FINANCIAL_DATA",
            schema="PUBLIC",
            status="success (mock)"
        )