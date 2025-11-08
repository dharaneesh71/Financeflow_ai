from typing import TypedDict, List
from app.models import (
    ExtractionResult, 
    FinancialInsight, 
    DatabaseSchema,
    DeploymentResult,
    ProcessingStatus
)
from app.agents.extractor import DocumentExtractor
from app.agents.analyzer import FinancialAnalyzer
from app.agents.schema_designer import SchemaDesigner
from backend.app.agents.snowflake_deployer import SnowflakeDeployer

class PipelineState(TypedDict):
    """State for the processing pipeline"""
    file_paths: List[str]
    extraction_results: List[ExtractionResult]
    analysis: FinancialInsight
    schema: DatabaseSchema
    deployment_result: DeploymentResult
    status_updates: List[ProcessingStatus]
    error: str

class FinancePipeline:
    """Main orchestrator"""
    
    def __init__(self):
        self.extractor = DocumentExtractor()
        self.analyzer = FinancialAnalyzer()
        self.designer = SchemaDesigner()
        self.deployer = SnowflakeDeployer()
    
    async def run(self, file_paths: List[str]) -> PipelineState:
        """Run the complete pipeline"""
        state: PipelineState = {
            "file_paths": file_paths,
            "extraction_results": [],
            "analysis": None,
            "schema": None,
            "deployment_result": None,
            "status_updates": [],
            "error": ""
        }
        
        try:
            for file_path in file_paths:
                result = await self.extractor.extract_from_document(file_path)
                state["extraction_results"].append(result)
            
            state["analysis"] = await self.analyzer.analyze(state["extraction_results"])
            state["schema"] = await self.designer.design_schema(
                state["extraction_results"],
                state["analysis"]
            )
            state["deployment_result"] = await self.deployer.deploy_schema(
                state["schema"],
                state["extraction_results"]
            )
            
        except Exception as e:
            state["error"] = str(e)
        
        return state