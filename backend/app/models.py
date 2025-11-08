from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class DocumentType(str, Enum):
    """Types of financial documents"""
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    UNKNOWN = "unknown"

class ExtractedField(BaseModel):
    """A single extracted field from a document"""
    field_name: str
    value: float
    confidence: float
    data_type: str = "currency"

class ExtractionResult(BaseModel):
    """Result of document extraction"""
    document_type: DocumentType
    period: str
    extracted_fields: List[ExtractedField]
    metadata: Dict[str, Any] = {}

class FinancialInsight(BaseModel):
    """Financial analysis insights"""
    document_type: str
    time_period: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    detected_relationships: List[Dict[str, Any]] = []
    suggested_metrics: List[str] = []
    data_quality: Dict[str, float] = {}
    issues: List[str] = []
    insights: List[str] = []

class TableColumn(BaseModel):
    """Database table column definition"""
    name: str
    type: str
    constraints: str = ""

class TableSchema(BaseModel):
    """Database table schema"""
    table_name: str
    columns: List[TableColumn]
    indexes: List[str] = []

class DatabaseSchema(BaseModel):
    """Complete database schema design"""
    tables: List[TableSchema]
    relationships: List[Dict[str, str]] = []
    validation_rules: List[str] = []
    clustering_recommendations: List[Dict[str, Any]] = []
    ddl_sql: str = ""

class DeploymentResult(BaseModel):
    """Result of Snowflake deployment"""
    tables_created: int
    rows_loaded: int
    database: str
    schema: str
    status: str

class ProcessRequest(BaseModel):
    """Request to process documents"""
    file_paths: List[str]

class ProcessResponse(BaseModel):
    """Complete processing response"""
    extraction_results: List[ExtractionResult]
    analysis: FinancialInsight
    schema: DatabaseSchema
    deployment: DeploymentResult