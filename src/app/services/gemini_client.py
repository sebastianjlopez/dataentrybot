"""
Client for Google Gemini Vision API.
Handles image/document processing and data extraction.
"""
import google.generativeai as genai
from typing import Optional, Dict, Any
import logging
from src.app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Gemini Vision API."""
    
    def __init__(self):
        """Initialize Gemini client with API key."""
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision')
        logger.info("Gemini client initialized")
    
    async def process_image(
        self, 
        image_data: bytes, 
        mime_type: str = "image/jpeg",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an image using Gemini Vision.
        
        Args:
            image_data: Binary image data
            mime_type: MIME type of the image
            prompt: Optional custom prompt for extraction
            
        Returns:
            Dictionary with extracted data
        """
        try:
            # Default prompt for general document extraction
            default_prompt = """
            Analiza esta imagen y extrae toda la información relevante.
            Si es un cheque, identifica:
            - CUIT del librador
            - Banco
            - Fecha de emisión
            - Fecha de pago
            - Importe
            - Número de cheque
            - CBU o CUIT del beneficiario (si aparece)
            
            Responde en formato JSON estructurado.
            """
            
            extraction_prompt = prompt or default_prompt
            
            # Prepare image part
            import PIL.Image
            import io
            
            image = PIL.Image.open(io.BytesIO(image_data))
            
            # Generate content
            response = self.model.generate_content([
                extraction_prompt,
                image
            ])
            
            # Parse response
            extracted_text = response.text
            
            logger.info(f"Gemini extraction completed. Response length: {len(extracted_text)}")
            
            return {
                "extracted_text": extracted_text,
                "raw_response": response.text,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing image with Gemini: {str(e)}")
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
        Process a cheque image with specific extraction prompt.
        
        Args:
            image_data: Binary image data
            mime_type: MIME type of the image
            
        Returns:
            Dictionary with structured cheque data
        """
        cheque_prompt = """
        Analiza esta imagen de un cheque argentino y extrae la siguiente información en formato JSON:
        
        {
            "cuit_librador": "CUIT del librador (formato XX-XXXXXXXX-X)",
            "banco": "Nombre del banco",
            "fecha_emision": "Fecha de emisión (YYYY-MM-DD)",
            "fecha_pago": "Fecha de pago o vencimiento (YYYY-MM-DD)",
            "importe": número en formato decimal,
            "numero_cheque": "Número de cheque",
            "cbu_beneficiario": "CBU o CUIT del beneficiario si aparece"
        }
        
        Si algún campo no se puede identificar, usa una cadena vacía o 0 según corresponda.
        Responde SOLO con el JSON, sin texto adicional.
        """
        
        result = await self.process_image(image_data, mime_type, cheque_prompt)
        
        # Try to parse JSON from response
        import json
        import re
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', result.get("extracted_text", ""), re.DOTALL)
            if json_match:
                cheque_data = json.loads(json_match.group())
                result["cheque_data"] = cheque_data
            else:
                result["cheque_data"] = {}
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse JSON from Gemini response: {e}")
            result["cheque_data"] = {}
        
        return result

