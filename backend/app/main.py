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

app = FastAPI(title="FinanceFlow AI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agents
extractor = DocumentExtractor()
analyzer = FinancialAnalyzer()
schema_designer = SchemaDesigner()
deployer = SnowflakeDeployer()

# Upload directory
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"status": "FinanceFlow AI is running", "version": "1.0"}

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload files to server"""
    print(f"\n📤 UPLOAD REQUEST: Received {len(files)} files")
    
    uploaded_files = []
    for file in files:
        file_path = UPLOAD_DIR / file.filename
        
        print(f"  - Saving: {file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_files.append(str(file_path))
        print(f"  ✅ Saved: {file_path}")
    
    return {
        "message": f"Uploaded {len(uploaded_files)} files",
        "files": uploaded_files
    }

@app.post("/api/process", response_model=ProcessResponse)
async def process_documents(request: ProcessRequest):
    """Process uploaded documents"""
    print(f"\n🔄 PROCESS REQUEST: Processing {len(request.file_paths)} files")
    print(f"Files: {request.file_paths}")
    
    try:
        # Step 1: Extract data from documents
        print("\n📋 STEP 1: EXTRACTION")
        extraction_results = []
        for file_path in request.file_paths:
            print(f"  🔍 Extracting: {file_path}")
            result = await extractor.extract_from_document(file_path)
            extraction_results.append(result)
            print(f"  ✅ Extracted {len(result.extracted_fields)} fields from {file_path}")
        
        # Step 2: Analyze extracted data
        print("\n🤖 STEP 2: ANALYSIS")
        analysis = await analyzer.analyze(extraction_results)
        print(f"  ✅ Analysis complete: {analysis.document_type}")
        
        # Step 3: Design database schema
        print("\n🏗️ STEP 3: SCHEMA DESIGN")
        schema = await schema_designer.design_schema(extraction_results, analysis)
        print(f"  ✅ Schema designed: {len(schema.tables)} tables")
        
        # Step 4: Deploy to Snowflake
        print("\n❄️ STEP 4: SNOWFLAKE DEPLOYMENT")
        deployment = await deployer.deploy(schema, extraction_results)
        print(f"  ✅ Deployed: {deployment.rows_loaded} rows loaded")
        
        response = ProcessResponse(
            extraction_results=extraction_results,
            analysis=analysis,
            schema=schema,
            deployment=deployment
        )
        
        print("\n✅ PROCESSING COMPLETE!")
        print(f"  - Documents: {len(extraction_results)}")
        print(f"  - Tables: {len(schema.tables)}")
        print(f"  - Rows: {deployment.rows_loaded}")
        
        return response
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)