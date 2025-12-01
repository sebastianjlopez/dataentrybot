"""
Client for Google Gemini LLM with Vision capabilities.
Uses Gemini 2.5 (latest version) with advanced reasoning for intelligent document processing.
"""
import google.generativeai as genai
from typing import Optional, Dict, Any
import logging
from src.app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Gemini 2.5 LLM (with vision) for intelligent document processing."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize Gemini client with API key.
        
        Args:
            model_name: Model to use. If None, uses model from settings.
                Options:
                - "gemini-2.5-flash": Fast and efficient (recommended for most cases)
                - "gemini-2.5-pro": More powerful reasoning (for complex cases)
        """
        genai.configure(api_key=settings.gemini_api_key)
        model_to_use = model_name or settings.gemini_model
        self.model = genai.GenerativeModel(model_to_use)
        self.model_name = model_to_use
        logger.info(f"Gemini 2.5 client initialized with model: {model_to_use}")
    
    async def process_image(
        self, 
        image_data: bytes, 
        mime_type: str = "image/jpeg",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an image using Gemini LLM with vision capabilities.
        Uses advanced reasoning to understand document structure and context.
        
        Args:
            image_data: Binary image data
            mime_type: MIME type of the image
            prompt: Optional custom prompt for extraction
            
        Returns:
            Dictionary with extracted data
        """
        try:
            # Default prompt with reasoning instructions
            default_prompt = """
            Analiza esta imagen de manera inteligente y razona sobre su contenido.
            
            INSTRUCCIONES:
            1. Primero, identifica el TIPO de documento (cheque, factura, recibo, etc.)
            2. Analiza la ESTRUCTURA del documento para entender dónde está cada información
            3. Extrae la información relevante razonando sobre el contexto
            
            Si es un CHEQUE ARGENTINO, identifica y razona sobre:
            - CUIT del librador: Busca en la sección del librador, puede estar en formato XX-XXXXXXXX-X o sin guiones
            - Banco: Identifica el nombre del banco emisor (puede estar en el logo o texto)
            - Fecha de emisión: Busca la fecha donde dice "fecha" o "emisión"
            - Fecha de pago/vencimiento: Busca donde dice "pagar a" o "vencimiento"
            - Importe: Busca el monto en números y también en letras para validar
            - Número de cheque: Busca el número único del cheque
            - CBU/CUIT beneficiario: Si aparece en el cheque
            
            RAZONAMIENTO:
            - Si un campo no está claro, razona sobre dónde debería estar según la estructura típica de cheques argentinos
            - Valida que los datos sean consistentes (ej: el importe en números debe coincidir con el de letras)
            - Si hay ambigüedad, indica tu razonamiento
            
            Responde en formato JSON estructurado con los campos extraídos.
            """
            
            extraction_prompt = prompt or default_prompt
            
            # Prepare image part - handle both images and PDFs
            import PIL.Image
            import io
            
            # Check if it's a PDF
            if mime_type == "application/pdf":
                # Convert PDF to image (all pages)
                from pdf2image import convert_from_bytes
                from PIL import Image
                logger.info("Converting PDF to image (all pages)...")
                images = convert_from_bytes(image_data, first_page=1, last_page=10)
                if images:
                    if len(images) == 1:
                        image = images[0]
                        logger.info(f"PDF converted to image: {image.size}")
                    else:
                        # Combine multiple pages
                        total_height = sum(img.height for img in images)
                        max_width = max(img.width for img in images)
                        image = Image.new('RGB', (max_width, total_height), color='white')
                        y_offset = 0
                        for img in images:
                            image.paste(img, (0, y_offset))
                            y_offset += img.height
                        logger.info(f"PDF converted to combined image ({len(images)} pages): {image.size}")
                else:
                    raise ValueError("Could not convert PDF to image")
            else:
                # It's a regular image
                image = PIL.Image.open(io.BytesIO(image_data))
            
            # Generate content with reasoning
            # Gemini 2.5 supports better structured outputs
            generation_config = {
                "temperature": 0.1,  # Lower temperature for more consistent extraction
                "top_p": 0.95,
                "top_k": 40,
            }
            
            response = self.model.generate_content(
                [extraction_prompt, image],
                generation_config=generation_config
            )
            
            # Parse response
            extracted_text = response.text
            
            logger.info(f"Gemini LLM extraction completed. Response length: {len(extracted_text)}")
            
            return {
                "extracted_text": extracted_text,
                "raw_response": response.text,
                "success": True,
                "model_used": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Error processing image with Gemini LLM: {str(e)}")
            return {
                "extracted_text": "",
                "raw_response": "",
                "success": False,
                "error": str(e)
            }
    
    async def process_cheque(
        self, 
        image_data: bytes, 
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Process a cheque image using advanced reasoning to understand structure and extract data.
        
        Args:
            image_data: Binary image data
            mime_type: MIME type of the image
            
        Returns:
            Dictionary with structured cheque data
        """
        # Handle PDF conversion if needed
        if mime_type == "application/pdf":
            from pdf2image import convert_from_bytes
            logger.info("Converting PDF to image (processing all pages for multiple cheques)...")
            # Convert all pages (up to 10 pages max to avoid memory issues)
            images = convert_from_bytes(image_data, first_page=1, last_page=10)
            if images:
                # Combine all pages into a single image (vertically stacked)
                # This allows Gemini to see all cheques at once
                from PIL import Image
                import io
                
                if len(images) == 1:
                    # Single page, use it directly
                    img_byte_arr = io.BytesIO()
                    images[0].save(img_byte_arr, format='PNG')
                    image_data = img_byte_arr.getvalue()
                    logger.info("PDF converted to PNG image (1 page)")
                else:
                    # Multiple pages, combine them
                    total_height = sum(img.height for img in images)
                    max_width = max(img.width for img in images)
                    combined = Image.new('RGB', (max_width, total_height), color='white')
                    
                    y_offset = 0
                    for img in images:
                        combined.paste(img, (0, y_offset))
                        y_offset += img.height
                    
                    img_byte_arr = io.BytesIO()
                    combined.save(img_byte_arr, format='PNG')
                    image_data = img_byte_arr.getvalue()
                    logger.info(f"PDF converted to PNG image ({len(images)} pages combined)")
                
                mime_type = "image/png"
            else:
                raise ValueError("Could not convert PDF to image")
        
        cheque_prompt = """
Analiza esta imagen de cheques argentinos y extrae TODOS los cheques encontrados.

RESPONDE ÚNICAMENTE CON ESTE JSON (sin texto adicional, sin markdown, sin explicaciones):

{
  "cheques": [
    {
      "cuit_librador": "30-69163759-6",
      "banco": "BANCO CREDICOOP",
      "fecha_emision": "2025-03-14",
      "fecha_pago": "2025-03-31",
      "importe": 1000000.00,
      "numero_cheque": "59503890",
      "cbu_beneficiario": null
    }
  ]
}

INSTRUCCIONES:
- Si hay múltiples cheques, agrega más objetos al array "cheques"
- cuit_librador: formato XX-XXXXXXXX-X (normaliza si viene sin guiones)
- banco: nombre completo del banco
- fecha_emision: formato YYYY-MM-DD (convierte "14 de marzo de 2025" a "2025-03-14")
- fecha_pago: formato YYYY-MM-DD
- importe: número decimal (ej: 1000000.00, 516099.40)
- numero_cheque: string con el número
- cbu_beneficiario: string o null

IMPORTANTE: Responde SOLO con el JSON, nada más.
        """
        
        result = await self.process_image(image_data, mime_type, cheque_prompt)
        
        # Try to parse JSON from response with improved extraction
        import json
        import re
        
        try:
            # Improved JSON extraction - handles nested objects and arrays
            text = result.get("extracted_text", "").strip()
            
            # Try to find JSON block (may be wrapped in markdown code blocks)
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',  # JSON in markdown code block
                r'```\s*(\{.*?\})\s*```',       # JSON in code block
                r'(\{.*\})',                    # Any JSON object (supports nested with DOTALL)
            ]
            
            cheque_data = {}
            for pattern in json_patterns:
                json_match = re.search(pattern, text, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(1)
                        parsed = json.loads(json_str)
                        
                        # Normalize structure: always use "cheques" array format
                        if "cheques" in parsed and isinstance(parsed["cheques"], list):
                            # Already in correct format
                            cheque_data = parsed
                        elif isinstance(parsed, list):
                            # Array at root level, wrap it
                            cheque_data = {"cheques": parsed}
                        elif isinstance(parsed, dict):
                            # Single cheque object, wrap in array
                            cheque_data = {"cheques": [parsed]}
                        else:
                            logger.warning(f"Unexpected JSON structure: {type(parsed)}")
                            cheque_data = {"cheques": []}
                        break
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON decode error with pattern {pattern}: {e}")
                        continue
            
            # If no JSON found, try to extract key-value pairs manually
            if not cheque_data or "cheques" not in cheque_data:
                logger.warning("Could not find valid JSON with 'cheques' array, attempting manual extraction")
                logger.debug(f"Response text (first 500 chars): {text[:500]}")
                # Fallback: try to extract individual fields using regex
                fallback_data = self._extract_fields_fallback(text)
                if fallback_data:
                    cheque_data = {"cheques": [fallback_data]}
                else:
                    cheque_data = {"cheques": []}
            
            # Ensure we always have the "cheques" array
            if "cheques" not in cheque_data:
                if cheque_data:
                    cheque_data = {"cheques": [cheque_data]}
                else:
                    cheque_data = {"cheques": []}
            
            result["cheque_data"] = cheque_data
            cheque_count = len(cheque_data.get("cheques", []))
            logger.info(f"Successfully extracted {cheque_count} cheque(s) from document")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON from Gemini response: {e}")
            logger.debug(f"Response text: {result.get('extracted_text', '')[:500]}")
            result["cheque_data"] = {}
        
        return result
    
    def _extract_fields_fallback(self, text: str) -> Dict[str, Any]:
        """
        Fallback method to extract fields if JSON parsing fails.
        Uses regex to find key-value pairs.
        """
        import re
        fields = {}
        
        # Extract common fields using regex
        patterns = {
            "cuit_librador": r'["\']?cuit_librador["\']?\s*[:=]\s*["\']?([^"\',}\]]+)["\']?',
            "banco": r'["\']?banco["\']?\s*[:=]\s*["\']?([^"\',}\]]+)["\']?',
            "importe": r'["\']?importe["\']?\s*[:=]\s*([0-9.]+)',
            "numero_cheque": r'["\']?numero_cheque["\']?\s*[:=]\s*["\']?([^"\',}\]]+)["\']?',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields[field] = match.group(1).strip()
        
        return fields


