from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
from pathlib import Path
import traceback

from app.agents.orchestrator import FinancePipeline, MetricExtractionPipeline, PipelineState
from app.models import (
    ProcessRequest, ProcessResponse,
    SuggestMetricsRequest, SuggestMetricsResponse, MetricDefinition,
    ExtractMetricsRequest, ExtractMetricsResponse,
    ExtractMarkdownRequest, ExtractMarkdownResponse
)
from app.config import get_settings

app = FastAPI(title="FinanceFlow AI", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get settings
settings = get_settings()

# Upload directory
UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize pipelines
finance_pipeline = None
metric_pipeline = None

def get_pipelines():
    """Lazy initialization of LangGraph pipelines"""
    global finance_pipeline, metric_pipeline
    
    if finance_pipeline is None:
        print("\n🚀 Initializing LangGraph Pipelines...")
        finance_pipeline = FinancePipeline()
        metric_pipeline = MetricExtractionPipeline()
        print("✅ All pipelines initialized\n")
    
    return finance_pipeline, metric_pipeline

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("\n" + "="*60)
    print("🚀 FinanceFlow AI Backend Starting...")
    print("="*60 + "\n")
    get_pipelines()
    print("✅ Backend ready at http://localhost:8000")
    print("📚 API Docs at http://localhost:8000/docs\n")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "FinanceFlow AI",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    fin_pipe, met_pipe = get_pipelines()
    return {
        "status": "healthy",
        "pipelines": {
            "finance_pipeline": "ready",
            "metric_pipeline": "ready"
        }
    }

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload financial documents"""
    print(f"\n{'='*60}")
    print(f"📤 UPLOAD REQUEST")
    print(f"{'='*60}")
    print(f"Received {len(files)} file(s)")
    
    uploaded_files = []
    
    for file in files:
        try:
            file_path = UPLOAD_DIR / file.filename
            
            print(f"  📄 {file.filename} ({file.content_type})")
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append(str(file_path))
            print(f"  ✅ Saved to: {file_path}")
            
        except Exception as e:
            print(f"  ❌ Error saving {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save {file.filename}: {str(e)}")
    
    print(f"\n✅ Upload complete: {len(uploaded_files)} files saved\n")
    
    return {
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
        "files": uploaded_files
    }

@app.post("/api/process", response_model=ProcessResponse)
async def process_documents(request: ProcessRequest):
    """Process uploaded financial documents through LangGraph pipeline"""
    
    print(f"\n{'='*60}")
    print(f"🔄 PROCESSING REQUEST (LangGraph)")
    print(f"{'='*60}")
    print(f"Files to process: {len(request.file_paths)}")
    for path in request.file_paths:
        print(f"  - {path}")
    print()
    
    try:
        # Validate file paths
        for file_path in request.file_paths:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Get pipeline
        finance_pipe, _ = get_pipelines()
        
        # Prepare initial state for FinancePipeline
        initial_state: PipelineState = {
            "file_paths": request.file_paths,
            "database_name": settings.snowflake_database,
            "schema_name": settings.snowflake_schema,
            "user_prompt": request.user_prompt or "",
            "selected_metrics": [],
            "markdown_paths": [],
            "extraction_results": [],
            "analysis": None,
            "schema": None,
            "deployment_result": None,
            "stop_after": request.stop_after or "all",
            "error": ""
        }
        
        # Run the LangGraph pipeline
        print(f"{'='*60}")
        print(f"🔄 Running LangGraph FinancePipeline...")
        print(f"{'='*60}\n")
        
        final_state = await finance_pipe.app.ainvoke(initial_state)
        
        # Check for errors
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
        
        # Build response
        response = ProcessResponse(
            extraction_results=final_state.get("extraction_results", []),
            analysis=final_state.get("analysis"),
            schema=final_state.get("schema"),
            deployment=final_state.get("deployment_result")
        )
        
        print(f"{'='*60}")
        print(f"✅ PROCESSING COMPLETE!")
        print(f"{'='*60}\n")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {str(e)}")
        print(f"{'='*60}\n")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/api/extract-markdown", response_model=ExtractMarkdownResponse)
async def extract_markdown(request: ExtractMarkdownRequest):
    """Extract markdown from a document file"""
    
    print(f"\n{'='*60}")
    print(f"📄 MARKDOWN EXTRACTION REQUEST")
    print(f"{'='*60}")
    print(f"File path: {request.file_path}")
    print(f"Output directory: {request.output_dir}")
    print()
    
    try:
        # Check if file exists
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_path}")
        
        # Use extractor directly for this granular endpoint
        from app.agents.extractor import DocumentExtractor
        extractor = DocumentExtractor()
        markdown_path = await extractor.extract_markdown_from_document(
            file_path=request.file_path,
            output_dir=request.output_dir or settings.upload_dir
        )
        
        print(f"✅ Markdown extraction complete\n")
        
        return ExtractMarkdownResponse(
            markdown_path=markdown_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {str(e)}")
        print(f"{'='*60}\n")
        traceback.print_exc()
        return ExtractMarkdownResponse(
            markdown_path="",
            error=str(e)
        )

@app.post("/api/suggest-metrics", response_model=SuggestMetricsResponse)
async def suggest_metrics(request: SuggestMetricsRequest):
    """Suggest metrics that can be extracted from a markdown file"""
    
    print(f"\n{'='*60}")
    print(f"💡 METRIC SUGGESTION REQUEST")
    print(f"{'='*60}")
    print(f"Markdown path: {request.markdown_path}")
    if request.user_prompt:
        print(f"User prompt: {request.user_prompt}")
    print()
    
    try:
        # Check if markdown file exists
        if not os.path.exists(request.markdown_path):
            raise HTTPException(status_code=404, detail=f"Markdown file not found: {request.markdown_path}")
        
        # Use extractor directly for this granular endpoint
        from app.agents.extractor import DocumentExtractor
        extractor = DocumentExtractor()
        
        # Suggest metrics
        result = await extractor.suggest_metrics_from_markdown(
            markdown_path=request.markdown_path,
            user_prompt=request.user_prompt
        )
        
        # Convert to response model
        if result.get("error"):
            return SuggestMetricsResponse(
                suggested_metrics=[],
                error=result.get("error")
            )
        
        # Convert metrics to MetricDefinition objects
        metrics = [
            MetricDefinition(**metric)
            for metric in result.get("suggested_metrics", [])
        ]
        
        print(f"✅ Suggested {len(metrics)} metrics\n")
        
        return SuggestMetricsResponse(
            suggested_metrics=metrics,
            reasoning=result.get("reasoning")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {str(e)}")
        print(f"{'='*60}\n")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Metric suggestion failed: {str(e)}")

@app.post("/api/extract-metrics", response_model=ExtractMetricsResponse)
async def extract_metrics(request: ExtractMetricsRequest):
    """Extract metrics from a markdown file using LandingAI ADE"""
    
    print(f"\n{'='*60}")
    print(f"🔍 METRIC EXTRACTION REQUEST")
    print(f"{'='*60}")
    print(f"Markdown path: {request.markdown_path}")
    print(f"Metrics to extract: {len(request.metrics)}")
    for metric in request.metrics:
        print(f"  - {metric.name} ({metric.type}): {metric.description}")
    print()
    
    try:
        # Check if markdown file exists
        if not os.path.exists(request.markdown_path):
            raise HTTPException(status_code=404, detail=f"Markdown file not found: {request.markdown_path}")
        
        # Use extractor directly for this granular endpoint
        from app.agents.extractor import DocumentExtractor
        extractor = DocumentExtractor()
        
        # Convert MetricDefinition to dict for extractor
        metrics_dict = [
            {
                "name": metric.name,
                "type": metric.type,
                "description": metric.description
            }
            for metric in request.metrics
        ]
        
        # Extract metrics
        result = await extractor.extract_metrics_from_markdown(
            markdown_path=request.markdown_path,
            metrics=metrics_dict,
            model=request.model
        )
        
        if result.get("error"):
            return ExtractMetricsResponse(
                extraction={},
                metrics=request.metrics,
                error=result.get("error")
            )
        
        print(f"✅ Extraction complete\n")
        
        return ExtractMetricsResponse(
            extraction=result.get("extraction", {}),
            metrics=request.metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {str(e)}")
        print(f"{'='*60}\n")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Metric extraction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)