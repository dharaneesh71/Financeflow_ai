import asyncio
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from app.config import get_settings
import traceback # Import traceback for error logging

# Import models (ProcessingStatus is NOT imported)
from app.models import (
    ExtractionResult, 
    FinancialInsight, 
    DatabaseSchema,
    DeploymentResult
)

# Import agents
from app.agents.extractor import DocumentExtractor
from app.agents.analyzer import FinancialAnalyzer
from app.agents.schema_designer import SchemaDesigner
from app.agents.snowflake_deployer import SnowflakeDeployer

settings = get_settings()

# --- ORIGINAL FINANCIAL STATEMENT PIPELINE ---

class PipelineState(TypedDict):
    """State for the original financial statement processing pipeline"""
    file_paths: List[str]
    extraction_results: List[ExtractionResult]
    analysis: FinancialInsight
    schema: DatabaseSchema
    deployment_result: DeploymentResult
    # status_updates: List[ProcessingStatus] # <-- THIS LINE IS REMOVED
    error: str
    database_name: str
    schema_name: str
    user_prompt: str  
    selected_metrics: List[Dict[str, Any]]
    markdown_paths: List[str]
    stop_after: str  # "extract" | "analyze" | "schema" | "deploy" | "all" - controls which step to stop after

class FinancePipeline:
    """
    Original orchestrator for end-to-end financial statement processing.
    """
    
    def __init__(self):
        self.extractor = DocumentExtractor()
        self.analyzer = FinancialAnalyzer()
        self.designer = SchemaDesigner()
        self.deployer = SnowflakeDeployer()
        self.app = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(PipelineState)
        workflow.add_node("extract_documents", self.extract_documents_node)
        workflow.add_node("analyze_data", self.analyze_data_node)
        workflow.add_node("design_schema", self.design_schema_node)
        workflow.add_node("deploy_to_snowflake", self.deploy_to_snowflake_node)
        workflow.set_entry_point("extract_documents")
        
        # Conditional edges - check if we should continue or stop after each step
        workflow.add_conditional_edges(
            "extract_documents",
            self.should_continue_after_extract,
            {
                "continue": "analyze_data",
                "stop": END
            }
        )
        workflow.add_conditional_edges(
            "analyze_data",
            self.should_continue_after_analyze,
            {
                "continue": "design_schema",
                "stop": END
            }
        )
        workflow.add_conditional_edges(
            "design_schema",
            self.should_continue_after_schema,
            {
                "continue": "deploy_to_snowflake",
                "stop": END
            }
        )
        workflow.add_edge("deploy_to_snowflake", END)
        return workflow.compile()
    
    def should_continue_after_extract(self, state: PipelineState) -> str:
        """Check if we should continue after extraction"""
        stop_after = state.get("stop_after", "all")
        # Stop after extraction only if stop_after is "extract"
        if stop_after == "extract":
            return "stop"
        # Otherwise continue to analysis
        return "continue"
    
    def should_continue_after_analyze(self, state: PipelineState) -> str:
        """Check if we should continue after analysis"""
        stop_after = state.get("stop_after", "all")
        # Stop after analysis only if stop_after is "analyze"
        if stop_after == "analyze":
            return "stop"
        # Otherwise continue to schema design
        return "continue"
    
    def should_continue_after_schema(self, state: PipelineState) -> str:
        """Check if we should continue after schema design"""
        stop_after = state.get("stop_after", "all")
        # Stop after schema only if stop_after is "schema"
        if stop_after == "schema":
            return "stop"
        # Otherwise continue to deployment (or "deploy" or "all")
        return "continue"

    # --- Node Implementations for FinancePipeline ---
    
    async def extract_documents_node(self, state: PipelineState) -> dict:
        print("--- (LangGraph) 1. Starting Document Extraction ---")
        file_paths = state["file_paths"]
        extraction_results = []
        for file_path in file_paths:
            result = await self.extractor.extract_from_document(file_path)
            extraction_results.append(result)
        return {"extraction_results": extraction_results}

    async def analyze_data_node(self, state: PipelineState) -> dict:
        print("--- (LangGraph) 2. Starting Financial Analysis ---")
        analysis = await self.analyzer.analyze(state["extraction_results"])
        return {"analysis": analysis}

    async def design_schema_node(self, state: PipelineState) -> dict:
        print("--- (LangGraph) 3. Starting Schema Design ---")
        schema = await self.designer.design_schema(
            extraction_results=state["extraction_results"],
            analysis=state["analysis"]
        )
        return {"schema": schema}

    async def deploy_to_snowflake_node(self, state: PipelineState) -> dict:
        print("--- (LangGraph) 4. Starting Snowflake Deployment ---")
        # Note: deployer uses settings.snowflake_database and settings.snowflake_schema
        # The database_name and schema_name in state are stored but not passed to deployer
        # (deployer method signature doesn't include these parameters)
        deployment_result = await self.deployer.deploy(
            schema=state["schema"],
            extraction_results=state["extraction_results"]
        )
        return {"deployment_result": deployment_result}
    
    async def run(self, *args, **kwargs) -> PipelineState:
        # (This is just a placeholder, the logic is in MetricExtractionPipeline)
        pass 

# --- NEW: METRIC EXTRACTION PIPELINE (FOR UI) ---

class MetricState(TypedDict):
    """
    State for the new UI-driven metric extraction pipeline.
    """
    # Inputs
    current_step: str # "suggest" or "process"
    file_paths: List[str]
    user_prompt: str
    selected_metrics: List[Dict[str, Any]]
    database_name: str
    schema_name: str
    
    # Internal state
    markdown_paths: List[str]
    
    # Outputs
    suggested_metrics: List[Dict[str, Any]]
    reasoning: str
    schema: DatabaseSchema
    deployment_result: DeploymentResult
    extracted_metrics: Dict[str, Any]
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

        # --- Define Nodes ---
        # Routing node (passthrough - just routes based on state)
        workflow.add_node("router", self.router_node)
        
        # "Suggest" Branch
        workflow.add_node("extract_markdown", self.extract_markdown_node)
        workflow.add_node("suggest_metrics", self.suggest_metrics_node)
        
        # "Process" Branch
        workflow.add_node("extract_metrics", self.extract_metrics_node)
        workflow.add_node("design_metrics_schema", self.design_metrics_schema_node)
        workflow.add_node("deploy_metrics", self.deploy_metrics_node)

        # --- Define Edges ---
        # Set router as entry point
        workflow.set_entry_point("router")
        
        # Conditional routing from router node
        workflow.add_conditional_edges(
            "router",
            self.should_suggest_or_process,
            {
                "suggest": "extract_markdown",
                "process": "extract_metrics"
            }
        )
        
        # "Suggest" flow
        workflow.add_edge("extract_markdown", "suggest_metrics")
        workflow.add_edge("suggest_metrics", END) # Stop after suggesting
        
        # "Process" flow
        workflow.add_edge("extract_metrics", "design_metrics_schema")
        workflow.add_edge("design_metrics_schema", "deploy_metrics")
        workflow.add_edge("deploy_metrics", END) # Stop after deploying

        return workflow.compile()

    # --- Routing Logic ---
    
    async def router_node(self, state: MetricState) -> dict:
        """Router node - passthrough that allows conditional routing"""
        # This node doesn't modify state, it just allows us to route
        return {}
    
    def should_suggest_or_process(self, state: MetricState) -> str:
        """Determines which branch of the graph to run."""
        if state.get("current_step") == "process":
            return "process"
        return "suggest"

    # --- "Suggest" Branch Nodes ---

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

    # --- "Process" Branch Nodes ---

    async def extract_metrics_node(self, state: MetricState) -> dict:
        print("--- (Metric Graph) 2a. Extracting Metrics ---")
        # This node just aggregates extracted data. Deployment node handles looping.
        # We'll extract from the *first* doc to show in the UI.
        # The deploy node will handle extraction for *all* docs.
        first_md_path = state["markdown_paths"][0]
        extraction_data = await self.extractor.extract_metrics_from_markdown(
            markdown_path=first_md_path,
            metrics=state["selected_metrics"]
        )
        return {"extracted_metrics": extraction_data.get("extraction", {})}

    async def design_metrics_schema_node(self, state: MetricState) -> dict:
        print("--- (Metric Graph) 2b. Designing Schema ---")
        # Use extracted_metrics from state if available, otherwise pass None
        # The schema designer only needs the metrics definitions, not the extracted values
        db_schema = await self.designer.design_schema(
            extracted_metrics=state.get("extracted_metrics"),
            metrics=state["selected_metrics"]
        )
        return {"schema": db_schema}

    async def deploy_metrics_node(self, state: MetricState) -> dict:
        print("--- (Metric Graph) 2c. Deploying Metrics ---")
        total_rows_loaded = 0
        final_deployment_result = None
        extracted_metrics_by_document = {}  # Store metrics by document name
        
        # Step 1: Create schema once (outside the loop)
        if state["markdown_paths"]:
            # Get extraction data from first document to design schema
            first_md_path = state["markdown_paths"][0]
            first_doc_name = (first_md_path.split('/')[-1]).split('.')[0]
            
            first_extraction_data = await self.extractor.extract_metrics_from_markdown(
                markdown_path=first_md_path,
                metrics=state["selected_metrics"]
            )
            
            if "error" not in first_extraction_data and first_extraction_data.get("extraction"):
                # Create schema once
                schema_result = await self.designer.design_schema(
                    extracted_metrics=first_extraction_data["extraction"],
                    metrics=state["selected_metrics"]
                )
                
                # Create database schema once
                schema_deployment = await self.deployer.create_schema_if_not_exists(schema_result)
                print(f"  ✅ Schema created: {schema_deployment.tables_created} tables")
                
                final_deployment_result = schema_deployment
            else:
                print("  ❌ Failed to extract metrics from first document for schema design")
                return {"deployment_result": None, "extracted_metrics": {}, "extracted_metrics_by_document": {}}
        
        # Step 2: Process each document and insert as separate row
        for md_path in state["markdown_paths"]:
            doc_name = (md_path.split('/')[-1]).split('.')[0]
            
            # Extract metrics for this document
            extraction_data = await self.extractor.extract_metrics_from_markdown(
                markdown_path=md_path,
                metrics=state["selected_metrics"]
            )
            
            if "error" in extraction_data or not extraction_data.get("extraction"):
                print(f"Skipping {doc_name}, extraction failed.")
                continue
            
            # Store metrics by document for frontend display
            extracted_metrics_by_document[doc_name] = extraction_data["extraction"]
            
            # Insert this document's metrics as a separate row
            rows_inserted = await self.deployer.insert_metrics_row(
                extracted_metrics=extraction_data["extraction"],
                metrics=state["selected_metrics"],
                document_name=doc_name
            )
            total_rows_loaded += rows_inserted
        
        # Update deployment result with total rows
        if final_deployment_result:
            final_deployment_result.rows_loaded = total_rows_loaded
            final_deployment_result.status = "success"
        
        print(f"  ✅ Total rows inserted: {total_rows_loaded}")
        
        return {
            "deployment_result": final_deployment_result,
            "extracted_metrics": extracted_metrics_by_document,  # Legacy field - first document's metrics
            "extracted_metrics_by_document": extracted_metrics_by_document  # New field - all documents
        }

    # --- Main .run() Method ---
    
    async def run(self, state: MetricState) -> MetricState:
        """
        Runs the appropriate branch of the graph based on the
        'current_step' provided in the initial state.
        """
        try:
            return await self.app.ainvoke(state)
        except Exception as e:
            traceback.print_exc()
            state["error"] = str(e)
            return state