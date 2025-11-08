from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class DocumentType(str, Enum):
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    UNKNOWN = "unknown"

class ExtractedField(BaseModel):
    field_name: str
    value: float
    confidence: float
    data_type: str = "currency"

class ExtractionResult(BaseModel):
    document_type: DocumentType
    period: str
    extracted_fields: List[ExtractedField]
    metadata: Dict[str, Any] = {}

class FinancialInsight(BaseModel):
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
    name: str
    type: str
    constraints: str = ""

class TableSchema(BaseModel):
    table_name: str
    columns: List[TableColumn]
    indexes: List[str] = []

class DatabaseSchema(BaseModel):
    tables: List[TableSchema]
    relationships: List[Dict[str, str]] = []
    validation_rules: List[str] = []
    clustering_recommendations: List[Dict[str, Any]] = []
    ddl_sql: str = ""

class DeploymentResult(BaseModel):
    tables_created: int
    rows_loaded: int
    database: str
    schema: str
    status: str

class ProcessRequest(BaseModel):
    file_paths: List[str]

class ProcessResponse(BaseModel):
    extraction_results: List[ExtractionResult]
    analysis: FinancialInsight
    schema: DatabaseSchema
    deployment: DeploymentResult