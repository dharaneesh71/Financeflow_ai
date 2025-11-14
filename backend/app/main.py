from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
import shutil
from pathlib import Path
import traceback
from datetime import time
from app.agents.orchestrator import MetricExtractionPipeline, MetricState
from app.models import ProcessRequest, ProcessResponse, MetricDefinition
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

def get_pipeline():
    """Lazy initialization of LangGraph pipelines"""
    global finance_pipeline, metric_pipeline
    
    if finance_pipeline is None:
        print("\n🚀 Initializing LangGraph Pipeline...")
        metric_pipeline = MetricExtractionPipeline()
        print("✅ Pipeline initialized\n")
    
    return metric_pipeline

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("\n" + "="*60)
    print("🚀 FinanceFlow AI Backend Starting...")
    print("="*60 + "\n")
    get_pipeline()
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
    met_pipe = get_pipeline()
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
    """Process uploaded financial documents through LangGraph MetricExtractionPipeline"""
    
    print(f"\n{'='*60}")
    print(f"🔄 PROCESSING REQUEST (MetricExtractionPipeline)")
    print(f"{'='*60}")
    print(f"Files to process: {len(request.file_paths)}")
    for path in request.file_paths:
        print(f"  - {path}")
    print(f"Selected metrics: {len(request.selected_metrics) if request.selected_metrics else 0}")
    print()
    
    try:
        # Validate file paths
        for file_path in request.file_paths:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        # Get pipeline
        metric_pipe = get_pipeline()
        
        # Determine workflow: if selected_metrics provided, use "process" branch, else "suggest" branch
        has_selected_metrics = request.selected_metrics and len(request.selected_metrics) > 0
        current_step = "process" if has_selected_metrics else "suggest"
        
        # Convert MetricDefinition to dict for pipeline
        selected_metrics_dict = []
        if request.selected_metrics:
            selected_metrics_dict = [
                {
                    "name": metric.name,
                    "type": metric.type,
                    "description": metric.description
                }
                for metric in request.selected_metrics
            ]
        
        # For process step, if we have file_paths but no markdown_paths, extract markdown first
        markdown_paths = []
        if current_step == "process" and request.file_paths:
            # Extract markdown from files if not already extracted
            from app.agents.extractor import DocumentExtractor
            extractor = DocumentExtractor()
            print(f"  📄 Extracting markdown from {len(request.file_paths)} file(s) for processing...")
            for file_path in request.file_paths:
                try:
                    md_path = await extractor.extract_markdown_from_document(
                        file_path=file_path,
                        output_dir=settings.upload_dir
                    )
                    markdown_paths.append(md_path)
                except Exception as e:
                    print(f"  ⚠️  Error extracting markdown from {file_path}: {e}")
                    # Continue with other files
            print(f"  ✅ Extracted {len(markdown_paths)} markdown file(s)")
        
        # Prepare initial state for MetricExtractionPipeline
        initial_state: MetricState = {
            "current_step": current_step,
            "file_paths": request.file_paths if current_step == "suggest" else [],
            "markdown_paths": markdown_paths if current_step == "process" else [],  # Will be populated by suggest step
            "user_prompt": request.user_prompt or "",
            "selected_metrics": selected_metrics_dict,
            "database_name": settings.snowflake_database,
            "schema_name": settings.snowflake_schema,
            "suggested_metrics": [],
            "reasoning": "",
            "schema": None,
            "deployment_result": None,
            "extracted_metrics": {},
            "error": ""
        }
        
        # Run the LangGraph pipeline
        print(f"{'='*60}")
        print(f"🔄 Running LangGraph MetricExtractionPipeline ({current_step} branch)...")
        print(f"{'='*60}\n")
        
        final_state = await metric_pipe.app.ainvoke(initial_state)
        
        # Check for errors
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
        
        # Build response based on which branch was executed
        if current_step == "suggest":
            # Suggest branch: return suggested metrics and markdown paths
            suggested_metrics = [
                MetricDefinition(**metric)
                for metric in final_state.get("suggested_metrics", [])
            ]
            
            response = ProcessResponse(
                markdown_paths=final_state.get("markdown_paths", []),
                suggested_metrics=suggested_metrics,
                reasoning=final_state.get("reasoning"),
                success=True
            )
            
            print(f"{'='*60}")
            print(f"✅ SUGGESTION COMPLETE!")
            print(f"   Suggested {len(suggested_metrics)} metrics")
            print(f"{'='*60}\n")
            
        else:
            # Process branch: return extracted metrics, schema, and deployment
            response = ProcessResponse(
                markdown_paths=final_state.get("markdown_paths", []),
                extracted_metrics=final_state.get("extracted_metrics", {}),  # Legacy - first doc only
                extracted_metrics_by_document=final_state.get("extracted_metrics_by_document", {}),  # New - all docs
                schema=final_state.get("schema"),
                deployment=final_state.get("deployment_result"),
                success=True
            )
            
            print(f"{'='*60}")
            print(f"✅ PROCESSING COMPLETE!")
            if final_state.get("schema"):
                print(f"   Created {len(final_state['schema'].tables)} tables")
            if final_state.get("deployment_result"):
                print(f"   Loaded {final_state['deployment_result'].rows_loaded} rows")
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


@app.post("/api/logs")
async def add_log_entry(request: Dict[str, Any]):
    """Add a new log entry"""
    try:
        log_entry = {
            "id": int(time.time() * 1000),  # timestamp-based ID
            "message": request.get("message", ""),
            "type": request.get("type", "info"),
            "timestamp": request.get("timestamp", "")
        }
        # logs_store.append(log_entry)
        # # Keep only last 1000 logs to prevent memory issues
        # if len(logs_store) > 1000:
        #     logs_store.pop(0)
        # return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add log: {str(e)}")

# @app.get("/api/logs")
# async def get_logs():
#     """Get all log entries"""
#     try:
#         return {"logs": logs_store}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)