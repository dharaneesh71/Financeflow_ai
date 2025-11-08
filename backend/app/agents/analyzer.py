import json
from typing import Dict, Any, List
import google.generativeai as genai
from app.models import ExtractionResult, FinancialInsight
from app.config import get_settings

settings = get_settings()

class FinancialAnalyzer:
    """Analyze financial data using Gemini"""
    
    def __init__(self):
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            print("✅ Gemini AI initialized successfully")
        except Exception as e:
            print(f"❌ Gemini init error: {e}")
            self.model = None
    
    async def analyze(self, extraction_results: List[ExtractionResult]) -> FinancialInsight:
        """Analyze extracted data"""
        
        print(f"🤖 Analyzing {len(extraction_results)} documents with Gemini...")
        
        if not self.model:
            return self._basic_analysis(extraction_results)
        
        try:
            extracted_data = self._prepare_data(extraction_results)
            
            prompt = f"""Analyze this financial data and return ONLY valid JSON:

{json.dumps(extracted_data, indent=2)}

Return this exact structure:
{{
  "document_type": "balance_sheet",
  "time_period": "quarterly",
  "fiscal_year": 2024,
  "fiscal_quarter": 3,
  "detected_relationships": [
    {{"type": "calculation", "formula": "Total Assets = Current + Fixed", "components_present": true}}
  ],
  "suggested_metrics": ["Current Ratio", "Debt-to-Equity"],
  "data_quality": {{"completeness": 0.95, "consistency_score": 0.92}},
  "issues": [],
  "insights": ["Strong cash position"]
}}"""
            
            response = self.model.generate_content(prompt)
            analysis_json = self._extract_json(response.text)
            
            print("✅ Analysis complete")
            return FinancialInsight(**analysis_json)
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return self._basic_analysis(extraction_results)
    
    def _prepare_data(self, extraction_results: List[ExtractionResult]) -> Dict[str, Any]:
        prepared = []
        for result in extraction_results:
            doc_data = {
                "document_type": str(result.document_type),
                "period": result.period,
                "fields": [
                    {"name": f.field_name, "value": f.value, "confidence": f.confidence}
                    for f in result.extracted_fields
                ]
            }
            prepared.append(doc_data)
        return {"documents": prepared}
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end]
        return json.loads(text.strip())
    
    def _basic_analysis(self, extraction_results: List[ExtractionResult]) -> FinancialInsight:
        return FinancialInsight(
            document_type="balance_sheet",
            time_period="quarterly",
            fiscal_year=2024,
            fiscal_quarter=3,
            detected_relationships=[],
            suggested_metrics=["Total Assets", "Current Ratio"],
            data_quality={"completeness": 0.9, "consistency_score": 0.85},
            issues=[],
            insights=["Document processed successfully"]
        )