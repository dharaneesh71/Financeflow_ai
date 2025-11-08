import os
import json
import requests
from typing import List, Dict, Any
from app.models import ExtractionResult, ExtractedField, DocumentType
from app.config import get_settings

settings = get_settings()

class DocumentExtractor:
    """Extract financial data using LandingAI"""
    
    def __init__(self):
        self.api_key = settings.landingai_api_key
        self.endpoint = "https://api.landing.ai/v1/agent/text-prompt"
        
        if not self.api_key:
            print("⚠️ WARNING: LANDINGAI_API_KEY not set, using mock data")
        else:
            print("✅ LandingAI initialized successfully")
    
    async def extract_from_document(self, file_path: str) -> ExtractionResult:
        """Extract data from document"""
        
        if not self.api_key:
            print(f"⚠️ Using mock extraction for: {file_path}")
            return self._mock_extraction(file_path)
        
        print(f"🔍 LandingAI extracting: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            prompt = """Analyze this financial document and extract ALL numerical data.

Return ONLY valid JSON in this format:
{
  "document_type": "balance_sheet",
  "period": "Q3 2024",
  "extracted_fields": [
    {"field_name": "Cash", "value": 25000.00, "confidence": 0.98, "data_type": "currency"},
    {"field_name": "Accounts Receivable", "value": 50000.00, "confidence": 0.96, "data_type": "currency"}
  ]
}

Extract EVERY line item with numbers."""

            files = {'images': (os.path.basename(file_path), file_content)}
            data = {'text_prompt': prompt}
            headers = {'apikey': self.api_key}
            
            response = requests.post(
                self.endpoint,
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ LandingAI error: {response.status_code}")
                return self._mock_extraction(file_path)
            
            result = response.json()
            extracted_text = result.get('text', '')
            
            # Parse JSON
            result_text = extracted_text.strip()
            if '```json' in result_text:
                start = result_text.find('```json') + 7
                end = result_text.find('```', start)
                result_text = result_text[start:end]
            
            result_json = json.loads(result_text.strip())
            
            fields = [ExtractedField(**field) for field in result_json.get('extracted_fields', [])]
            
            doc_type_str = result_json.get('document_type', 'unknown').lower()
            doc_type_map = {
                'balance_sheet': DocumentType.BALANCE_SHEET,
                'income_statement': DocumentType.INCOME_STATEMENT,
                'cash_flow': DocumentType.CASH_FLOW,
            }
            doc_type = doc_type_map.get(doc_type_str, DocumentType.UNKNOWN)
            
            print(f"✅ Extracted {len(fields)} fields")
            
            return ExtractionResult(
                document_type=doc_type,
                period=result_json.get('period', 'Unknown'),
                extracted_fields=fields,
                metadata={'source': 'landingai', 'file': os.path.basename(file_path)}
            )
            
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return self._mock_extraction(file_path)
    
    def _mock_extraction(self, file_path: str) -> ExtractionResult:
        """Mock extraction for testing"""
        return ExtractionResult(
            document_type=DocumentType.BALANCE_SHEET,
            period="Q3 2024",
            extracted_fields=[
                ExtractedField(field_name="Cash", value=25000, confidence=0.98, data_type="currency"),
                ExtractedField(field_name="Accounts Receivable", value=50000, confidence=0.96, data_type="currency"),
                ExtractedField(field_name="Inventory", value=20000, confidence=0.95, data_type="currency"),
                ExtractedField(field_name="Total Current Assets", value=95000, confidence=0.97, data_type="currency"),
                ExtractedField(field_name="Fixed Assets", value=108200, confidence=0.96, data_type="currency"),
                ExtractedField(field_name="Total Assets", value=203200, confidence=0.98, data_type="currency"),
            ],
            metadata={"source": "mock", "file": os.path.basename(file_path)}
        )