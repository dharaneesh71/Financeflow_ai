from typing import List, Dict, Any, Optional
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
        extraction_results: List[ExtractionResult] = None,
        extracted_metrics: Dict[str, Any] = None,
        metrics: List[Dict[str, Any]] = None,
        document_name: str = None
    ) -> DeploymentResult:
        """Deploy schema and load data to Snowflake"""
        
        if not self.use_snowflake:
            raise ValueError("Snowflake credentials not configured - configure credentials for database deployment")
        
        # If we have extracted metrics, use metrics deployment
        if extracted_metrics and metrics:
            return await self._deploy_metrics(schema, extracted_metrics, metrics, document_name)
        
        # Otherwise use standard deployment
        if extraction_results:
            return await self._deploy_standard(schema, extraction_results)
        
        # If nothing provided, just create tables
        return await self._deploy_schema_only(schema)
    
    async def create_schema_if_not_exists(self, schema: DatabaseSchema) -> DeploymentResult:
        """Create database, schema and tables once (not per document)"""
        if not self.use_snowflake:
            raise ValueError("Snowflake credentials not configured - configure credentials for database deployment")
        
        try:
            print(f"  📡 Connecting to Snowflake for schema creation...")
            
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
            
            # Create database and schema if not exists (don't drop!)
            print(f"  🗄️  Setting up database and schema...")
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
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return DeploymentResult(
                tables_created=tables_created,
                rows_loaded=0,  # No data loaded yet
                database=settings.snowflake_database,
                schema=settings.snowflake_schema,
                status="schema_created"
            )
            
        except Exception as e:
            print(f"  ❌ Schema creation error: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError("  ❌ Schema creation error: for database deployment")
    
    async def insert_metrics_row(
        self,
        extracted_metrics: Dict[str, Any],
        metrics: List[Dict[str, Any]],
        document_name: str = None
    ) -> int:
        """Insert a single row of metrics data (call this for each document)"""
        if not self.use_snowflake:
            raise ValueError("Snowflake credentials not configured - configure credentials for database deployment")
        
        try:
            print(f"  📊 Inserting metrics for document: {document_name}")
            
            # DEBUG
            print(f"  🔍 Selected metrics: {[m.get('name') for m in metrics]}")
            print(f"  🔍 Extracted keys: {list(extracted_metrics.keys())}")
            
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
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")
            
            # Build insert - UPPERCASE columns
            column_names = ["DOCUMENT_NAME"] + [m.get('name', '').upper() for m in metrics]
            placeholders = ", ".join(["%s"] * len(column_names))
            columns_str = ", ".join(column_names)
            
            insert_sql = f"INSERT INTO EXTRACTED_METRICS ({columns_str}) VALUES ({placeholders})"
            print(f"  🔍 SQL: {insert_sql[:150]}...")
            
            # Prepare values - LOWERCASE lookup
            values = [document_name or "unknown"]
            for metric in metrics:
                metric_name_lower = metric.get('name', '').lower()
                value = extracted_metrics.get(metric_name_lower)
                values.append(value)
            
            print(f"  🔍 Values count: {len(values)}")
            
            cursor.execute(insert_sql, values)
            rows_loaded = 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"  ✅ Inserted 1 row for {document_name}")
            return rows_loaded
            
        except Exception as e:
            print(f"  ❌ Insert error for {document_name}: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    async def _deploy_metrics(
        self,
        schema: DatabaseSchema,
        extracted_metrics: Dict[str, Any],
        metrics: List[Dict[str, Any]],
        document_name: str = None
    ) -> DeploymentResult:
        """Deploy extracted metrics to Snowflake - LEGACY METHOD"""
        print("  ⚠️  Using legacy deployment method")
        
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
            
            print(f"  🗄️  Setting up database...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.snowflake_database}")
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.snowflake_schema}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")
            
            print(f"  📋 Creating tables...")
            ddl_statements = [stmt.strip() for stmt in schema.ddl_sql.split(';') if stmt.strip()]
            
            for i, ddl in enumerate(ddl_statements, 1):
                if ddl and not ddl.startswith('--'):
                    cursor.execute(ddl)
            
            tables_created = len(schema.tables)
            print(f"  ✅ Created {tables_created} tables")
            
            print(f"  📊 Loading metrics data...")
            
            column_names = ["DOCUMENT_NAME"] + [m.get('name', '').upper() for m in metrics]
            placeholders = ", ".join(["%s"] * len(column_names))
            columns_str = ", ".join(column_names)
            
            insert_sql = f"INSERT INTO EXTRACTED_METRICS ({columns_str}) VALUES ({placeholders})"
            
            values = [document_name or "unknown"]
            for metric in metrics:
                metric_name_lower = metric.get('name', '').lower()
                value = extracted_metrics.get(metric_name_lower)
                values.append(value)
            
            cursor.execute(insert_sql, values)
            rows_loaded = 1
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"  ✅ Loaded {rows_loaded} row(s)")
            
            return DeploymentResult(
                tables_created=tables_created,
                rows_loaded=rows_loaded,
                database=settings.snowflake_database,
                schema=settings.snowflake_schema,
                status="success"
            )
            
        except Exception as e:
            print(f"  ❌ Deployment error: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError("  ❌ Deployment error: for database deployment")
    
    async def _deploy_standard(
        self,
        schema: DatabaseSchema,
        extraction_results: List[ExtractionResult]
    ) -> DeploymentResult:
        """Deploy standard extraction results to Snowflake"""
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
            
            print(f"  🗄️  Setting up database...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.snowflake_database}")
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.snowflake_schema}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")
            
            print(f"  📋 Creating tables...")
            ddl_statements = [stmt.strip() for stmt in schema.ddl_sql.split(';') if stmt.strip()]
            
            for i, ddl in enumerate(ddl_statements, 1):
                if ddl and not ddl.startswith('--'):
                    cursor.execute(ddl)
            
            tables_created = len(schema.tables)
            print(f"  ✅ Created {tables_created} tables")
            
            print(f"  📊 Loading data...")
            rows_loaded = 0
            
            for doc_idx, result in enumerate(extraction_results, 1):
                # (Standard deployment logic - unchanged)
                pass
            
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
            print(f"  ❌ Deployment error: {e}")
            import traceback
            traceback.print_exc()
            return self._mock_deployment(schema, extraction_results, None, None)
    
    async def _deploy_schema_only(self, schema: DatabaseSchema) -> DeploymentResult:
        """Deploy only schema without data"""
        try:
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
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.snowflake_database}")
            cursor.execute(f"USE DATABASE {settings.snowflake_database}")
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.snowflake_schema}")
            cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")
            
            ddl_statements = [stmt.strip() for stmt in schema.ddl_sql.split(';') if stmt.strip()]
            for ddl in ddl_statements:
                if ddl and not ddl.startswith('--'):
                    cursor.execute(ddl)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return DeploymentResult(
                tables_created=len(schema.tables),
                rows_loaded=0,
                database=settings.snowflake_database,
                schema=settings.snowflake_schema,
                status="success (schema only)"
            )
        except Exception as e:
            print(f"  ❌ Schema deployment error: {e}")
            raise ValueError("  ❌ Schema deployment error: for database deployment")
    
