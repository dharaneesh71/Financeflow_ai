import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from landingai_ade import LandingAIADE
from landingai_ade.lib import pydantic_to_json_schema
from pydantic import BaseModel, Field, create_model
import google.generativeai as genai
from app.models import ExtractionResult, ExtractedField, DocumentType
from app.config import get_settings

settings = get_settings()

class DocumentExtractor:
    """Extract financial data from documents using LandingAI"""
    
    def __init__(self):
        self.api_key = settings.landingai_api_key
        self.gemini_api_key = settings.gemini_api_key
        # self.endpoint = "https://api.landing.ai/v1/agent/text-prompt"
        self.use_landingai = bool(self.api_key)
        
        if self.use_landingai:
            try:
                self.client = LandingAIADE(
                    apikey=self.api_key,
                )
                print(f"✅ LandingAI ADE Extractor initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize LandingAI ADE: {e}")
                self.use_landingai = False
        else:
            print("⚠️  LandingAI API key not found - using mock extraction")
        
        # Initialize Gemini for metric suggestions
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                self.use_gemini = True
                print("✅ Gemini AI initialized for metric suggestions")
            except Exception as e:
                print(f"⚠️  Gemini initialization error: {e}")
                self.use_gemini = False
        else:
            self.use_gemini = False
            print("⚠️  Gemini API key not found - metric suggestions unavailable")
    
    async def extract_markdown_from_document(self, file_path: str, output_dir: str = "./") -> str:
        """Extract markdown from a document and save it to a file"""
        
        if not self.use_landingai:
            raise ValueError("LandingAI API not available")
        
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Use the LandingAI ADE client to parse the document
            response = self.client.parse(
                document=Path(file_path),
                model="dpt-2-latest",
            )

            if response.markdown:
                # Generate output filename based on input file
                input_filename = os.path.basename(file_path)
                base_name = os.path.splitext(input_filename)[0]
                markdown_filename = f"{base_name}.md"
                markdown_path = os.path.join(output_dir, markdown_filename)
                
                # Save markdown to file
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(response.markdown)
                
                print(f"✅ Markdown saved to: {markdown_path}")
                return markdown_path
            else:
                raise ValueError("No 'markdown' field found in the response")
                
        except Exception as e:
            print(f"  ⚠️  Error extracting markdown: {e}")
            raise
    
    async def extract_from_document(self, file_path: str) -> ExtractionResult:
        """Extract financial data from a document"""
        
        if not self.use_landingai:
            return self._mock_extraction(file_path)
        
        try:
            # Use the LandingAI ADE client to parse the document
            response = self.client.parse(
                document=Path(file_path),
                model="dpt-2-latest",
            )

            if not response.markdown:
                print("No 'markdown' field found in the response")
                return self._mock_extraction(file_path)
            
            markdown_content = response.markdown
            print(f"  ✅ Extracted markdown ({len(markdown_content)} chars)")
            
            # Parse markdown with Gemini to extract structured financial data
            if self.use_gemini:
                try:
                    result_json = await self._extract_structured_data_from_markdown(markdown_content)
                except Exception as e:
                    print(f"  ⚠️  Error parsing markdown with Gemini: {e}")
                    return self._mock_extraction(file_path)
            else:
                print("  ⚠️  Gemini not available, using mock data")
                return self._mock_extraction(file_path)
            
            # Build ExtractionResult from parsed JSON
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
            import traceback
            traceback.print_exc()
            return self._mock_extraction(file_path)
    
    async def _extract_structured_data_from_markdown(self, markdown_content: str) -> Dict[str, Any]:
        """Extract structured financial data from markdown using Gemini"""
        
        prompt = f"""Analyze this financial document markdown and extract ALL numerical data.

Return ONLY valid JSON in this exact format (no markdown, no explanations):
{{
  "document_type": "balance_sheet",
  "period": "Q3 2024",
  "extracted_fields": [
    {{
      "field_name": "Cash",
      "value": 25000.00,
      "confidence": 0.98,
      "data_type": "currency"
    }},
    {{
      "field_name": "Accounts Receivable",
      "value": 50000.00,
      "confidence": 0.96,
      "data_type": "currency"
    }}
  ]
}}

Extract EVERY financial line item you can find with its numerical value.

Markdown content:
{markdown_content[:5000]}
"""
        
        # Use asyncio.to_thread to run the synchronous Gemini API call in a thread pool
        import asyncio
        response = await asyncio.to_thread(self.gemini_model.generate_content, prompt)
        response_text = response.text
        
        # Parse JSON from response
        return self._parse_json_response(response_text)
    
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
    
    async def suggest_metrics_from_markdown(
        self, 
        markdown_path: str, 
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest metrics that can be extracted from markdown using Gemini"""
        
        if not self.use_gemini:
            return {
                "suggested_metrics": [],
                "error": "Gemini API not available"
            }
        
        try:
            # Read markdown file
            markdown_content = Path(markdown_path).read_text(encoding='utf-8')
            
            # Limit content size for Gemini (keep first 10000 chars, which is usually enough)
            # Gemini has context limits, but 10k chars should be fine for most documents
            max_chars = 10000
            if len(markdown_content) > max_chars:
                markdown_preview = markdown_content[:max_chars] + f"\n\n... (truncated, total length: {len(markdown_content)} characters)"
            else:
                markdown_preview = markdown_content
            
            # Build prompt for Gemini
            if user_prompt:
                prompt = f"""You are a financial data extraction expert. A user wants to extract specific metrics from a financial document.

User's requirements: {user_prompt}

Here is the markdown content of the document:
{markdown_preview}

Based on the user's requirements and the document content, suggest metrics that can be extracted. For each metric, provide:
1. The metric name (in snake_case for Python)
2. The data type (str, int, float, bool)
3. A clear description

Return ONLY valid JSON format (no markdown, no explanations):
{{
  "suggested_metrics": [
    {{
      "name": "account_holder_name",
      "type": "str",
      "description": "The name of the account holder"
    }},
    {{
      "name": "total_assets",
      "type": "float",
      "description": "Total assets amount"
    }}
  ],
  "reasoning": "Brief explanation of why these metrics are relevant"
}}"""
            else:
                prompt = f"""You are a financial data extraction expert. Analyze this financial document and suggest metrics that can be extracted.

Here is the markdown content of the document:
{markdown_preview}

Suggest relevant metrics that can be extracted from this document. For each metric, provide:
1. The metric name (in snake_case for Python)
2. The data type (str, int, float, bool)
3. A clear description

Focus on:
- Key financial figures (amounts, balances, totals)
- Identifiers (account numbers, names, dates)
- Counts (number of transactions, deposits, etc.)
- Calculated metrics (ratios, percentages)

Return ONLY valid JSON format (no markdown, no explanations):
{{
  "suggested_metrics": [
    {{
      "name": "account_holder_name",
      "type": "str",
      "description": "The name of the account holder"
    }},
    {{
      "name": "total_assets",
      "type": "float",
      "description": "Total assets amount"
    }},
    {{
      "name": "number_deposits",
      "type": "int",
      "description": "The number of deposits"
    }}
  ],
  "reasoning": "Brief explanation of why these metrics are relevant"
}}"""
            
            print(f"  🤖 Calling Gemini AI to suggest metrics...")
            response = self.gemini_model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end]
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end]
            
            # Parse JSON
            suggestions = json.loads(response_text.strip())
            
            print(f"  ✅ Suggested {len(suggestions.get('suggested_metrics', []))} metrics")
            
            return suggestions
            
        except Exception as e:
            print(f"  ⚠️  Error suggesting metrics: {e}")
            return {
                "suggested_metrics": [],
                "error": str(e)
            }
    
    def create_schema_from_metrics(self, metrics: List[Dict[str, Any]]) -> type[BaseModel]:
        """Create a dynamic Pydantic model from metric definitions"""
        
        fields = {}
        for metric in metrics:
            name = metric.get('name', '')
            metric_type = metric.get('type', 'str')
            description = metric.get('description', '')
            
            # Map string types to Python types
            type_mapping = {
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
            }
            
            python_type = type_mapping.get(metric_type, str)
            
            # Create Field with description
            fields[name] = (python_type, Field(description=description))
        
        # Create the model dynamically
        DynamicModel = create_model('ExtractionSchema', **fields)
        return DynamicModel
    
    async def extract_metrics_from_markdown(
        self,
        markdown_path: str,
        metrics: List[Dict[str, Any]],
        model: str = "extract-latest"
    ) -> Dict[str, Any]:
        """Extract metrics from markdown using LandingAI ADE extract method"""
        
        if not self.use_landingai:
            return {
                "extraction": {},
                "error": "LandingAI API not available"
            }
        
        try:
            # Create schema from metrics
            schema_class = self.create_schema_from_metrics(metrics)
            
            # Convert to JSON schema
            schema = pydantic_to_json_schema(schema_class)
            
            print(f"  📋 Created schema with {len(metrics)} metrics")
            print(f"  🔍 Extracting metrics using LandingAI ADE...")
            
            # Extract fields using LandingAI ADE
            response = self.client.extract(
                schema=schema,
                markdown=Path(markdown_path),
                model=model
            )
            
            print(f"  ✅ Extraction complete")
            
            # Return extraction results
            return {
                "extraction": response.extraction if hasattr(response, 'extraction') else {},
                "schema": schema,
                "metrics": metrics
            }
            
        except Exception as e:
            print(f"  ⚠️  Error extracting metrics: {e}")
            import traceback
            traceback.print_exc()
            return {
                "extraction": {},
                "error": str(e)
            }