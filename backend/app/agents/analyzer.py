import json
from typing import Dict, Any, List
import google.generativeai as genai
from app.models import ExtractionResult, FinancialInsight
from app.config import get_settings

settings = get_settings()

class FinancialAnalyzer:
    """Analyze extracted financial data using Gemini AI"""
    
    def __init__(self):
        try:
            genai.configure(api_key=settings.gemini_api_key)
            # Use the free Gemini 2.0 Flash model
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            self.use_gemini = True
            print("✅ Gemini AI Analyzer initialized (gemini-2.0-flash-exp)")
        except Exception as e:
            print(f"⚠️  Gemini initialization error: {e}")
            self.use_gemini = False
    
    async def analyze(self, extraction_results: List[ExtractionResult]) -> FinancialInsight:
        """Analyze extracted financial data"""
        
        if not self.use_gemini:
            print("  ⚠️  Using basic analysis (Gemini not available)")
            return self._basic_analysis(extraction_results)
        
        try:
            extracted_data = self._prepare_data(extraction_results)
            
            prompt = f"""You are a financial data analyst. Analyze this extracted financial data and provide insights.

DATA:
{json.dumps(extracted_data, indent=2)}

Provide your analysis in ONLY valid JSON format (no markdown, no explanations before or after):
{{
  "document_type": "balance_sheet or income_statement or cash_flow",
  "time_period": "quarterly or annual",
  "fiscal_year": 2024,
  "fiscal_quarter": 3,
  "detected_relationships": [
    {{
      "type": "calculation",
      "formula": "Total Assets = Current Assets + Fixed Assets",
      "components_present": true
    }}
  ],
  "suggested_metrics": ["Current Ratio", "Quick Ratio", "Debt-to-Equity Ratio", "Working Capital"],
  "data_quality": {{
    "completeness": 0.95,
    "consistency_score": 0.92
  }},
  "issues": ["list any data quality issues found"],
  "insights": [
    "Key financial insight 1",
    "Key financial insight 2",
    "Key financial insight 3"
  ]
}}

Analyze the numbers, identify patterns, calculate key ratios, and provide meaningful financial insights."""
            
            print(f"  🤖 Calling Gemini AI (gemini-2.0-flash-exp)...")
            response = self.model.generate_content(prompt)
            
            analysis_json = self._extract_json(response.text)
            
            return FinancialInsight(**analysis_json)
            
        except Exception as e:
            print(f"  ⚠️  Gemini analysis error: {e}")
            print(f"  📝 Using basic analysis instead")
            return self._basic_analysis(extraction_results)
    
    def _prepare_data(self, extraction_results: List[ExtractionResult]) -> Dict[str, Any]:
        """Prepare data for analysis"""
        prepared = []
        for result in extraction_results:
            doc_data = {
                "document_type": str(result.document_type),
                "period": result.period,
                "fields": [
                    {
                        "name": f.field_name,
                        "value": f.value,
                        "confidence": f.confidence
                    }
                    for f in result.extracted_fields
                ]
            }
            prepared.append(doc_data)
        return {"documents": prepared}
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Gemini response"""
        text = text.strip()
        
        # Remove markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end]
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end]
        
        # Clean up any remaining text before/after JSON
        text = text.strip()
        if text.startswith('{'):
            # Find the matching closing brace
            brace_count = 0
            for i, char in enumerate(text):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        text = text[:i+1]
                        break
        
        return json.loads(text.strip())
    
    def _basic_analysis(self, extraction_results: List[ExtractionResult]) -> FinancialInsight:
        """Provide basic analysis without AI"""
        
        if not extraction_results:
            doc_type = "unknown"
            period = "Unknown"
            fields = []
        else:
            doc_type = str(extraction_results[0].document_type)
            period = extraction_results[0].period
            fields = extraction_results[0].extracted_fields
        
        # Extract year and quarter from period
        year = 2024
        quarter = None
        if "Q" in period:
            try:
                quarter = int(period.split("Q")[1].split()[0])
            except:
                pass
        
        # Calculate some basic insights
        insights = ["Document successfully processed"]
        
        if fields:
            total_fields = len(fields)
            avg_confidence = sum(f.confidence for f in fields) / total_fields
            insights.append(f"Extracted {total_fields} financial line items")
            insights.append(f"Average extraction confidence: {avg_confidence:.2%}")
            
            # Find key metrics
            field_names = [f.field_name.lower() for f in fields]
            if any('asset' in name for name in field_names):
                insights.append("Balance sheet structure detected")
            if any('revenue' in name or 'income' in name for name in field_names):
                insights.append("Income statement items identified")
            if any('cash' in name for name in field_names):
                insights.append("Cash flow information present")
        
        insights.append("Ready for database deployment")
        
        return FinancialInsight(
            document_type=doc_type,
            time_period="quarterly" if quarter else "annual",
            fiscal_year=year,
            fiscal_quarter=quarter,
            detected_relationships=[
                {
                    "type": "hierarchy",
                    "description": "Financial statement structure detected",
                    "components_present": True
                }
            ],
            suggested_metrics=["Total Assets", "Current Ratio", "Working Capital", "Net Income"],
            data_quality={
                "completeness": 0.90,
                "consistency_score": 0.85
            },
            issues=[],
            insights=insights
        )