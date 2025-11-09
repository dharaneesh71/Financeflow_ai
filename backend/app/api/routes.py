from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import os
import aiofiles
from pathlib import Path
import traceback

# Import the orchestrators
from app.agents.orchestrator import FinancePipeline, MetricExtractionPipeline
# Import the state model for the new pipeline
from app.agents.orchestrator import MetricState

from app.config import get_settings

settings = get_settings()
router = APIRouter()

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

# Initialize pipelines
# We keep the old one in case you want to add routes for it
finance_pipeline = FinancePipeline()
metric_pipeline = MetricExtractionPipeline()

@router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload documents and return their server paths."""
    saved_paths = []
    
    try:
        for file in files:
            file_path = os.path.join(settings.upload_dir, file.filename)
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            saved_paths.append(file_path)
        
        return {"success": True, "files": saved_paths, "count": len(saved_paths)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@router.post("/suggest")
async def suggest_metrics(request: dict):
    """
    Takes file paths, generates markdown, and suggests metrics
    by running the "suggest" branch of the MetricExtractionPipeline.
    """
    file_paths = request.get("file_paths", [])
    if not file_paths:
        raise HTTPException(status_code=400, detail="No file_paths provided")

    try:
        # 1. Prepare the initial state
        initial_state: MetricState = {
            "current_step": "suggest",
            "file_paths": file_paths,
            "user_prompt": request.get("user_prompt"),
            # Set defaults for other fields
            "selected_metrics": [],
            "database_name": "",
            "schema_name": "",
            "markdown_paths": [],
            "suggested_metrics": [],
            "reasoning": "",
            "schema": None,
            "deployment_result": None,
            "extracted_metrics": {},
            "error": ""
        }

        # 2. Run the graph
        final_state = await metric_pipeline.app.ainvoke(initial_state)

        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])

        # 3. Return the results
        return {
            "success": True,
            "suggested_metrics": final_state["suggested_metrics"],
            "reasoning": final_state.get("reasoning", ""),
            "markdown_paths": final_state["markdown_paths"] # Send this back
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process_metrics")
async def process_metrics(request: dict):
    """
    Takes markdown paths, metrics, and DB info, and runs the
    "process" branch of the MetricExtractionPipeline.
    """
    try:
        markdown_paths = request.get("markdown_paths", [])
        selected_metrics = request.get("selected_metrics", [])
        
        if not markdown_paths or not selected_metrics:
            raise HTTPException(status_code=400, detail="markdown_paths and selected_metrics are required.")

        # 1. Prepare the initial state
        initial_state: MetricState = {
            "current_step": "process",
            "markdown_paths": markdown_paths,
            "selected_metrics": selected_metrics,
            "database_name": request.get("database_name", settings.snowflake_database),
            "schema_name": request.get("schema_name", settings.snowflake_schema),
            # Set defaults for other fields
            "file_paths": [],
            "user_prompt": "",
            "suggested_metrics": [],
            "reasoning": "",
            "schema": None,
            "deployment_result": None,
            "extracted_metrics": {},
            "error": ""
        }

        # 2. Run the graph
        final_state = await metric_pipeline.app.ainvoke(initial_state)

        if final_state.get("error") or not final_state.get("deployment_result"):
            raise HTTPException(status_code=500, detail=final_state.get("error", "Processing failed"))

        # 3. Return the results
        return {
            "success": True,
            "schema": final_state["schema"].dict() if final_state["schema"] else None,
            "deployment": final_state["deployment_result"].dict() if final_state["deployment_result"] else None,
            "extracted_metrics": final_state["extracted_metrics"],
            "error": ""
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}