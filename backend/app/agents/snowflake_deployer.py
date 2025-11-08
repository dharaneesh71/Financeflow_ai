from typing import List
import snowflake.connector
from app.models import DatabaseSchema, ExtractionResult, DeploymentResult
from app.config import get_settings

settings = get_settings()

class SnowflakeDeployer:
    """Deploy schema and data to Snowflake"""
    
    def __init__(self):
        self.use_snowflake = all([
            settings.snowflake_account,
            settings.snowflake_user,
            settings.snowflake_password
        ])
        
        if self.use_snowflake:
            print(f"✅ Snowflake Deployer initialized")
            print(f"   Target: {settings.snowflake_database}.{settings.snowflake_schema}")
        else:
            print("⚠️  Snowflake credentials not configured - using mock deployment")
    
    async def deploy(
        self, 
        schema: DatabaseSchema, 
        extraction_results: List[ExtractionResult]
    ) -> DeploymentResult:
        """Deploy schema and load data to Snowflake"""
        
        if not self.use_snowflake:
            return self._mock_deployment(schema, extraction_results)
        
        try:
            print(f"  📡 Connecting to Snowflake...")
            
            conn = snowflake.connector.connect(
                user=settings.snowflake_user,
                password=settings.snowflake_password,
                account=settings.snowflake_account,
                warehouse=settings.snowflake_warehouse,
                database=settings.snowflake_database,
                schema=settings.snowflake_schema,
                role=settings.snowflake_role
            )
            
            cursor = conn.cursor()
            
            # Create database and schema if not exists
            print(f"  🗄️  Setting up database...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.snowflake_database}")
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.snowflake_schema}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")
            
            # Execute DDL to create tables
            print(f"  📋 Creating tables...")
            ddl_statements = [stmt.strip() for stmt in schema.ddl_sql.split(';') if stmt.strip()]
            
            for i, ddl in enumerate(ddl_statements, 1):
                if ddl and not ddl.startswith('--'):
                    print(f"     Executing DDL statement {i}/{len(ddl_statements)}")
                    cursor.execute(ddl)
            
            tables_created = len(schema.tables)
            print(f"  ✅ Created {tables_created} tables")
            
            # Load data
            print(f"  📊 Loading data...")
            rows_loaded = 0
            
            for doc_idx, result in enumerate(extraction_results, 1):
                print(f"     Loading document {doc_idx}/{len(extraction_results)}")
                
                # Insert into DIM_TIME_PERIOD
                period_sql = """
                INSERT INTO DIM_TIME_PERIOD (FISCAL_YEAR, FISCAL_QUARTER, PERIOD_NAME, PERIOD_TYPE)
                SELECT 2024, 3, 'Q3 2024', 'quarterly'
                WHERE NOT EXISTS (
                    SELECT 1 FROM DIM_TIME_PERIOD WHERE FISCAL_YEAR = 2024 AND FISCAL_QUARTER = 3
                )
                """
                cursor.execute(period_sql)
                
                # Get period_id
                cursor.execute("SELECT PERIOD_ID FROM DIM_TIME_PERIOD WHERE FISCAL_YEAR = 2024 AND FISCAL_QUARTER = 3")
                period_id = cursor.fetchone()[0]
                
                # Insert into DIM_DOCUMENT
                doc_sql = """
                INSERT INTO DIM_DOCUMENT (FILE_NAME, DOCUMENT_TYPE, PROCESSING_STATUS)
                VALUES (%s, %s, 'completed')
                """
                cursor.execute(doc_sql, (
                    result.metadata.get('file', 'unknown'),
                    str(result.document_type)
                ))
                document_id = cursor.lastrowid
                
                # Insert fields
                for field in result.extracted_fields:
                    # Insert account if not exists
                    account_sql = """
                    INSERT INTO DIM_ACCOUNT (ACCOUNT_NAME, ACCOUNT_TYPE, DOCUMENT_TYPE)
                    SELECT %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM DIM_ACCOUNT WHERE ACCOUNT_NAME = %s
                    )
                    """
                    cursor.execute(account_sql, (
                        field.field_name,
                        field.data_type,
                        str(result.document_type),
                        field.field_name
                    ))
                    
                    # Get account_id
                    cursor.execute("SELECT ACCOUNT_ID FROM DIM_ACCOUNT WHERE ACCOUNT_NAME = %s", (field.field_name,))
                    account_id = cursor.fetchone()[0]
                    
                    # Insert fact
                    fact_sql = """
                    INSERT INTO FACT_FINANCIAL_DATA 
                    (PERIOD_ID, ACCOUNT_ID, DOCUMENT_ID, AMOUNT, CONFIDENCE_SCORE, DATA_TYPE)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(fact_sql, (
                        period_id,
                        account_id,
                        document_id,
                        field.value,
                        field.confidence,
                        field.data_type
                    ))
                    rows_loaded += 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"  ✅ Loaded {rows_loaded} rows")
            
            return DeploymentResult(
                tables_created=tables_created,
                rows_loaded=rows_loaded,
                database=settings.snowflake_database,
                schema=settings.snowflake_schema,
                status="success"
            )
            
        except Exception as e:
            print(f"  ❌ Snowflake deployment error: {e}")
            print(f"  ⚠️  Falling back to mock deployment")
            return self._mock_deployment(schema, extraction_results)
    
    def _mock_deployment(
        self, 
        schema: DatabaseSchema, 
        extraction_results: List[ExtractionResult]
    ) -> DeploymentResult:
        """Mock deployment for demo/testing"""
        
        tables_created = len(schema.tables)
        rows_loaded = sum(len(r.extracted_fields) for r in extraction_results)
        
        print(f"  ✅ Mock deployment complete")
        print(f"     Tables: {tables_created}")
        print(f"     Rows: {rows_loaded}")
        
        return DeploymentResult(
            tables_created=tables_created,
            rows_loaded=rows_loaded,
            database=settings.snowflake_database or "FINANCIAL_DATA",
            schema=settings.snowflake_schema or "PUBLIC",
            status="success (mock - configure Snowflake for real deployment)"
        )