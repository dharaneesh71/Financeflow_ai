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

class MetricDefinition(BaseModel):
    """Definition of a metric to extract"""
    name: str
    type: str  # str, int, float, bool
    description: str
    
class ProcessRequest(BaseModel):
    """Request to process documents"""
    file_paths: List[str]
    user_prompt: Optional[str] = None  # Optional prompt for metric suggestions
    selected_metrics: Optional[List[MetricDefinition]] = None  # Selected metrics for extraction
    stop_after: Optional[str] = "all"  # "extract" | "analyze" | "schema" | "deploy" | "all" - which step to stop after

class ProcessResponse(BaseModel):
    """Complete processing response"""
    markdown_paths: List[str] = []  # Markdown files extracted
    suggested_metrics: Optional[List[MetricDefinition]] = None  # AI-suggested metrics
    extracted_metrics: Optional[Dict[str, Any]] = None  # Extracted metric values (legacy - use extracted_metrics_by_document)
    extracted_metrics_by_document: Optional[Dict[str, Dict[str, Any]]] = None  # New: metrics by document name
    schema: Optional[DatabaseSchema] = None  # Optional - only present after processing
    deployment: Optional[DeploymentResult] = None  # Optional - only present after processing
    extraction_results: List[ExtractionResult] = []  # Legacy field for compatibility
    analysis: Optional[FinancialInsight] = None  # Legacy field for compatibility
    reasoning: Optional[str] = None  # Reasoning for metric suggestions
    success: Optional[bool] = True  # Success flag
class AnalysisQuery(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = []

class ChartSpec(BaseModel):
    chart_type: str  # 'line', 'bar', 'pie', 'table'
    title: str
    x_axis: str
    y_axis: str
    series: List[str]
    data: List[Dict[str, Any]]

class AnalysisResponse(BaseModel):
    summary: str
    insights: List[str]
    chart: Optional[ChartSpec] = None
    available_companies: Optional[List[str]] = None
    available_metrics: Optional[List[str]] = None
    error: Optional[str] = None