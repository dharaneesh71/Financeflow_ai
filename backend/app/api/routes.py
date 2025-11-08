from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import aiofiles
from pathlib import Path
from app.agents.orchestrator import FinancePipeline
from app.config import get_settings

settings = get_settings()
router = APIRouter()

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

pipeline = FinancePipeline()

@router.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload documents"""
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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process")
async def process_documents(request: dict):
    """Process documents"""
    try:
        file_paths = request.get("file_paths", [])
        result = await pipeline.run(file_paths)
        
        return {
            "success": not result.get("error"),
            "extraction_results": [r.dict() for r in result.get("extraction_results", [])],
            "analysis": result.get("analysis").dict() if result.get("analysis") else None,
            "schema": result.get("schema").dict() if result.get("schema") else None,
            "deployment": result.get("deployment_result").dict() if result.get("deployment_result") else None,
            "error": result.get("error", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}