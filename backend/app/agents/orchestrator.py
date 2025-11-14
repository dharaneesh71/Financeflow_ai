import asyncio
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from app.config import get_settings
import traceback

from app.models import (
    ExtractionResult, 
    FinancialInsight, 
    DatabaseSchema,
    DeploymentResult
)

from app.agents.extractor import DocumentExtractor
from app.agents.schema_designer import SchemaDesigner
from app.agents.snowflake_deployer import SnowflakeDeployer

settings = get_settings()

# --- METRIC EXTRACTION PIPELINE (FOR UI) ---

class MetricState(TypedDict):
    """
    State for the new UI-driven metric extraction pipeline.
    """
    current_step: str
    file_paths: List[str]
    user_prompt: str
    selected_metrics: List[Dict[str, Any]]
    database_name: str
    schema_name: str
    markdown_paths: List[str]
    suggested_metrics: List[Dict[str, Any]]
    reasoning: str
    schema: DatabaseSchema
    deployment_result: DeploymentResult
    extracted_metrics: Dict[str, Any]
    extracted_metrics_by_document: Dict[str, Dict[str, Any]]  # ADD THIS
    error: str

class MetricExtractionPipeline:
    """
    New LangGraph workflow to manage the multi-step UI flow:
    1. Suggest Metrics
    2. Process Metrics
    """
    
    def __init__(self):
        self.extractor = DocumentExtractor()
        self.designer = SchemaDesigner()
        self.deployer = SnowflakeDeployer()
        self.app = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(MetricState)

        workflow.add_node("router", self.router_node)
        workflow.add_node("extract_markdown", self.extract_markdown_node)
        workflow.add_node("suggest_metrics", self.suggest_metrics_node)
        workflow.add_node("extract_metrics", self.extract_metrics_node)
        workflow.add_node("design_metrics_schema", self.design_metrics_schema_node)
        workflow.add_node("deploy_metrics", self.deploy_metrics_node)

        workflow.set_entry_point("router")
        
        workflow.add_conditional_edges(
            "router",
            self.should_suggest_or_process,
            {
                "suggest": "extract_markdown",
                "process": "extract_metrics"
            }
        )
        
        workflow.add_edge("extract_markdown", "suggest_metrics")
        workflow.add_edge("suggest_metrics", END)
        
        workflow.add_edge("extract_metrics", "design_metrics_schema")
        workflow.add_edge("design_metrics_schema", "deploy_metrics")
        workflow.add_edge("deploy_metrics", END)

        return workflow.compile()

    async def router_node(self, state: MetricState) -> dict:
        return {}
    
    def should_suggest_or_process(self, state: MetricState) -> str:
        if state.get("current_step") == "process":
            return "process"
        return "suggest"

    async def extract_markdown_node(self, state: MetricState) -> dict:
        print("--- (Metric Graph) 1a. Extracting Markdown ---")
        markdown_paths = []
        for file_path in state["file_paths"]:
            md_path = await self.extractor.extract_markdown_from_document(
                file_path, 
                output_dir=settings.upload_dir
            )
            markdown_paths.append(md_path)
        return {"markdown_paths": markdown_paths}

    async def suggest_metrics_node(self, state: MetricState) -> dict:
        print("--- (Metric Graph) 1b. Suggesting Metrics ---")
        first_markdown_path = state["markdown_paths"][0]
        suggestions = await self.extractor.suggest_metrics_from_markdown(
            first_markdown_path, 
            state["user_prompt"]
        )
        return {
            "suggested_metrics": suggestions.get("suggested_metrics", []),
            "reasoning": suggestions.get("reasoning", "")
        }

    async def extract_metrics_node(self, state: MetricState) -> dict:
        """
        Extract metrics from ALL documents at once.
        This ensures we use the SAME metric definitions for all documents.
        """
        print("--- (Metric Graph) 2a. Extracting Metrics ---")
        
        extracted_metrics_by_document = {}
        
        # Extract from ALL documents using the SAME selected_metrics
        for md_path in state["markdown_paths"]:
            doc_name = md_path.replace('\\', '/').split('/')[-1].replace('.md', '')
            
            print(f"  🔍 Extracting from: {doc_name}")
            extraction_data = await self.extractor.extract_metrics_from_markdown(
                markdown_path=md_path,
                metrics=state["selected_metrics"]  # ALWAYS use the same metrics
            )
            
            if "error" not in extraction_data and extraction_data.get("extraction"):
                extracted_metrics_by_document[doc_name] = extraction_data["extraction"]
                print(f"  ✅ Extracted {len(extraction_data['extraction'])} metrics from {doc_name}")
            else:
                print(f"  ⚠️  Failed to extract from {doc_name}")
                extracted_metrics_by_document[doc_name] = {}
        
        # For backwards compatibility, store first document's metrics
        first_doc_metrics = {}
        if extracted_metrics_by_document:
            first_doc_metrics = list(extracted_metrics_by_document.values())[0]
        
        return {
            "extracted_metrics": first_doc_metrics,  # Legacy
            "extracted_metrics_by_document": extracted_metrics_by_document  # New
        }

    async def design_metrics_schema_node(self, state: MetricState) -> dict:
        print("--- (Metric Graph) 2b. Designing Schema ---")
        
        # Get first document's metrics for schema design (or empty dict if none)
        first_doc_metrics = state.get("extracted_metrics", {})
        
        db_schema = await self.designer.design_schema(
            extracted_metrics=first_doc_metrics,
            metrics=state["selected_metrics"]  # ALWAYS use selected_metrics
        )
        return {"schema": db_schema}

    async def deploy_metrics_node(self, state: MetricState) -> dict:
        """
        Deploy schema once, then insert each document as a separate row.
        CRITICAL: Use only the metrics from state["selected_metrics"]
        """
        print("--- (Metric Graph) 2c. Deploying Metrics ---")
        
        total_rows_loaded = 0
        final_deployment_result = None
        
        # Get the extracted metrics that were already extracted in extract_metrics_node
        extracted_metrics_by_document = state.get("extracted_metrics_by_document", {})
        
        if not extracted_metrics_by_document:
            print("  ⚠️  No metrics extracted, skipping deployment")
            return {
                "deployment_result": None,
                "extracted_metrics": {},
                "extracted_metrics_by_document": {}
            }
        
        # Step 1: Create schema ONCE using the selected_metrics
        first_doc_metrics = list(extracted_metrics_by_document.values())[0]
        
        schema_result = await self.designer.design_schema(
            extracted_metrics=first_doc_metrics,
            metrics=state["selected_metrics"]  # Use selected_metrics for schema
        )
        
        schema_deployment = await self.deployer.create_schema_if_not_exists(schema_result)
        print(f"  ✅ Schema created: {schema_deployment.tables_created} tables")
        
        final_deployment_result = schema_deployment
        
        # Step 2: Insert each document's extracted metrics
        for doc_name, doc_metrics in extracted_metrics_by_document.items():
            print(f"  📊 Inserting metrics for: {doc_name}")
            
            # Insert using the SAME selected_metrics list
            rows_inserted = await self.deployer.insert_metrics_row(
                extracted_metrics=doc_metrics,
                metrics=state["selected_metrics"],  # CRITICAL: Use selected_metrics
                document_name=doc_name
            )
            total_rows_loaded += rows_inserted
        
        # Update deployment result
        if final_deployment_result:
            final_deployment_result.rows_loaded = total_rows_loaded
            final_deployment_result.status = "success" if total_rows_loaded > 0 else "partial"
        
        print(f"  ✅ Total rows inserted: {total_rows_loaded}")
        
        return {
            "deployment_result": final_deployment_result,
            "extracted_metrics": first_doc_metrics,
            "extracted_metrics_by_document": extracted_metrics_by_document
        }

    async def run(self, state: MetricState) -> MetricState:
        """
        Runs the appropriate branch of the graph.
        """
        try:
            return await self.app.ainvoke(state)
        except Exception as e:
            traceback.print_exc()
            state["error"] = str(e)
            return state