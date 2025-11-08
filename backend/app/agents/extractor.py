import os
import json
import requests
from typing import List, Dict, Any
from app.models import ExtractionResult, ExtractedField, DocumentType
from app.config import get_settings

settings = get_settings()

class DocumentExtractor:
    """Extract financial data from documents using LandingAI"""
    
    def __init__(self):
        self.api_key = settings.landingai_api_key
        self.endpoint = "https://api.landing.ai/v1/agent/text-prompt"
        self.use_landingai = bool(self.api_key)
        
        if self.use_landingai:
            print("✅ LandingAI Extractor initialized")
        else:
            print("⚠️  LandingAI API key not found - using mock extraction")
    
    async def extract_from_document(self, file_path: str) -> ExtractionResult:
        """Extract financial data from a document"""
        
        if not self.use_landingai:
            return self._mock_extraction(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            prompt = self._build_extraction_prompt()
            
            files = {'images': (os.path.basename(file_path), file_content)}
            data = {'text_prompt': prompt}
            headers = {'apikey': self.api_key}
            
            print(f"  📤 Calling LandingAI API...")
            response = requests.post(
                self.endpoint,
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"  ⚠️  LandingAI returned status {response.status_code}, using mock data")
                return self._mock_extraction(file_path)
            
            result = response.json()
            extracted_text = result.get('text', '')
            
            # Parse JSON from response
            result_json = self._parse_json_response(extracted_text)
            
            # Build ExtractionResult
            fields = [ExtractedField(**field) for field in result_json.get('extracted_fields', [])]
            
            doc_type = self._map_document_type(result_json.get('document_type', 'unknown'))
            
            return ExtractionResult(
                document_type=doc_type,
                period=result_json.get('period', 'Unknown'),
                extracted_fields=fields,
                metadata={
                    'source': 'landingai',
                    'file': os.path.basename(file_path),
                    'confidence_avg': sum(f.confidence for f in fields) / len(fields) if fields else 0
                }
            )
            
        except Exception as e:
            print(f"  ⚠️  Extraction error: {e}, using mock data")
            return self._mock_extraction(file_path)
    
    def _build_extraction_prompt(self) -> str:
        """Build the prompt for LandingAI"""
        return """Analyze this financial document and extract ALL numerical data.

Return ONLY valid JSON in this exact format (no markdown, no explanations):
{
  "document_type": "balance_sheet",
  "period": "Q3 2024",
  "extracted_fields": [
    {
      "field_name": "Cash",
      "value": 25000.00,
      "confidence": 0.98,
      "data_type": "currency"
    },
    {
      "field_name": "Accounts Receivable",
      "value": 50000.00,
      "confidence": 0.96,
      "data_type": "currency"
    }
  ]
}

Extract EVERY financial line item you can find with its numerical value."""
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LandingAI response"""
        text = text.strip()
        
        # Remove markdown code blocks
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            text = text[start:end]
        elif '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            text = text[start:end]
        
        return json.loads(text.strip())
    
    def _map_document_type(self, doc_type_str: str) -> DocumentType:
        """Map string to DocumentType enum"""
        doc_type_map = {
            'balance_sheet': DocumentType.BALANCE_SHEET,
            'income_statement': DocumentType.INCOME_STATEMENT,
            'profit_loss': DocumentType.INCOME_STATEMENT,
            'p&l': DocumentType.INCOME_STATEMENT,
            'cash_flow': DocumentType.CASH_FLOW,
        }
        return doc_type_map.get(doc_type_str.lower(), DocumentType.UNKNOWN)
    
    def _mock_extraction(self, file_path: str) -> ExtractionResult:
        """Mock extraction for demo/testing"""
        filename = os.path.basename(file_path).lower()
        
        # Detect document type from filename
        if 'income' in filename or 'profit' in filename or 'p&l' in filename:
            doc_type = DocumentType.INCOME_STATEMENT
            fields = [
                ExtractedField(field_name="Revenue", value=523456.78, confidence=0.98, data_type="currency"),
                ExtractedField(field_name="Cost of Goods Sold", value=210000.00, confidence=0.96, data_type="currency"),
                ExtractedField(field_name="Gross Profit", value=313456.78, confidence=0.97, data_type="currency"),
                ExtractedField(field_name="Operating Expenses", value=125000.00, confidence=0.95, data_type="currency"),
                ExtractedField(field_name="Net Income", value=188456.78, confidence=0.97, data_type="currency"),
            ]
        elif 'cash' in filename:
            doc_type = DocumentType.CASH_FLOW
            fields = [
                ExtractedField(field_name="Operating Cash Flow", value=150000.00, confidence=0.98, data_type="currency"),
                ExtractedField(field_name="Investing Cash Flow", value=-50000.00, confidence=0.96, data_type="currency"),
                ExtractedField(field_name="Financing Cash Flow", value=-25000.00, confidence=0.95, data_type="currency"),
                ExtractedField(field_name="Net Cash Flow", value=75000.00, confidence=0.97, data_type="currency"),
            ]
        else:
            doc_type = DocumentType.BALANCE_SHEET
            fields = [
                ExtractedField(field_name="Cash", value=25000.00, confidence=0.98, data_type="currency"),
                ExtractedField(field_name="Accounts Receivable", value=50000.00, confidence=0.96, data_type="currency"),
                ExtractedField(field_name="Inventory", value=20000.00, confidence=0.95, data_type="currency"),
                ExtractedField(field_name="Total Current Assets", value=95000.00, confidence=0.97, data_type="currency"),
                ExtractedField(field_name="Fixed Assets", value=108200.00, confidence=0.96, data_type="currency"),
                ExtractedField(field_name="Total Assets", value=203200.00, confidence=0.98, data_type="currency"),
                ExtractedField(field_name="Accounts Payable", value=5000.00, confidence=0.95, data_type="currency"),
                ExtractedField(field_name="Total Liabilities", value=131250.00, confidence=0.97, data_type="currency"),
                ExtractedField(field_name="Owner's Equity", value=71950.00, confidence=0.96, data_type="currency"),
            ]
        
        return ExtractionResult(
            document_type=doc_type,
            period="Q3 2024",
            extracted_fields=fields,
            metadata={
                'source': 'mock',
                'file': os.path.basename(file_path),
                'note': 'Using mock data - configure LandingAI API key for real extraction'
            }
        )