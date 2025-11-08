from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
from pathlib import Path

from app.agents.extractor import DocumentExtractor
from app.agents.analyzer import FinancialAnalyzer
from app.agents.schema_designer import SchemaDesigner
from app.agents.snowflake_deployer import SnowflakeDeployer
from app.models import ProcessRequest, ProcessResponse

app = FastAPI(title="FinanceFlow AI", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize agents
extractor = None
analyzer = None
schema_designer = None
deployer = None

def get_agents():
    """Lazy initialization of agents"""
    global extractor, analyzer, schema_designer, deployer
    
    if extractor is None:
        print("\n🚀 Initializing AI Agents...")
        extractor = DocumentExtractor()
        analyzer = FinancialAnalyzer()
        schema_designer = SchemaDesigner()
        deployer = SnowflakeDeployer()
        print("✅ All agents initialized\n")
    
    return extractor, analyzer, schema_designer, deployer

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("\n" + "="*60)
    print("🚀 FinanceFlow AI Backend Starting...")
    print("="*60 + "\n")
    get_agents()
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
    ext, ana, sch, dep = get_agents()
    return {
        "status": "healthy",
        "agents": {
            "extractor": "ready",
            "analyzer": "ready",
            "schema_designer": "ready",
            "deployer": "ready"
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
    """Process uploaded financial documents through AI pipeline"""
    
    print(f"\n{'='*60}")
    print(f"🔄 PROCESSING REQUEST")
    print(f"{'='*60}")
    print(f"Files to process: {len(request.file_paths)}")
    for path in request.file_paths:
        print(f"  - {path}")
    print()
    
    try:
        ext, ana, sch, dep = get_agents()
        
        # STEP 1: Extract data
        print(f"{'='*60}")
        print(f"📋 STEP 1: DOCUMENT EXTRACTION")
        print(f"{'='*60}")
        
        extraction_results = []
        for file_path in request.file_paths:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
            
            print(f"\n🔍 Extracting: {os.path.basename(file_path)}")
            result = await ext.extract_from_document(file_path)
            extraction_results.append(result)
            print(f"✅ Extracted {len(result.extracted_fields)} fields")
        
        print(f"\n✅ Extraction Complete\n")
        
        # STEP 2: Analyze
        print(f"{'='*60}")
        print(f"🤖 STEP 2: FINANCIAL ANALYSIS")
        print(f"{'='*60}\n")
        
        analysis = await ana.analyze(extraction_results)
        print(f"✅ Analysis Complete\n")
        
        # STEP 3: Design schema
        print(f"{'='*60}")
        print(f"🏗️  STEP 3: SCHEMA DESIGN")
        print(f"{'='*60}\n")
        
        schema = await sch.design_schema(extraction_results, analysis)
        print(f"✅ Schema Designed: {len(schema.tables)} tables\n")
        
        # STEP 4: Deploy
        print(f"{'='*60}")
        print(f"❄️  STEP 4: SNOWFLAKE DEPLOYMENT")
        print(f"{'='*60}\n")
        
        deployment = await dep.deploy(schema, extraction_results)
        print(f"✅ Deployment Complete\n")
        
        response = ProcessResponse(
            extraction_results=extraction_results,
            analysis=analysis,
            schema=schema,
            deployment=deployment
        )
        
        print(f"{'='*60}")
        print(f"✅ PROCESSING COMPLETE!")
        print(f"{'='*60}\n")
        
        return response
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR: {str(e)}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)