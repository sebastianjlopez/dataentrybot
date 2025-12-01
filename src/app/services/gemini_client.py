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
            
            # Prepare image part
            import PIL.Image
            import io
            
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
        cheque_prompt = """
        Eres un experto en análisis de cheques argentinos usando Gemini 2.5. 
        Analiza esta imagen de un cheque y razona sobre su estructura para extraer la información con precisión.

        PROCESO DE RAZONAMIENTO (usando capacidades avanzadas de Gemini 2.5):
        1. ANÁLISIS ESTRUCTURAL:
           - Identifica las secciones del cheque: encabezado (banco, logo), datos del librador, 
             datos del beneficiario, montos (números y letras), fechas, número de cheque
           - Usa tu capacidad de razonamiento para entender el contexto visual
        
        2. EXTRACCIÓN INTELIGENTE:
           Para cada campo, razona:
           - ¿Dónde debería estar este dato según la estructura estándar de cheques argentinos?
           - ¿Qué formato tiene? (ej: CUIT puede estar con o sin guiones: 20-12345678-9 o 20123456789)
           - ¿Hay información que valide este dato? (ej: importe en números vs letras)
           - Si hay texto parcialmente oculto o borroso, razona sobre qué debería decir
        
        3. VALIDACIÓN Y CONSISTENCIA:
           - El importe en números debe coincidir con el de letras (valida ambos)
           - Las fechas deben ser lógicas (fecha_pago >= fecha_emision)
           - El CUIT debe tener formato válido (11 dígitos, normaliza a XX-XXXXXXXX-X)
           - El banco debe ser reconocible (puede estar en logo o texto)
        
        4. MANEJO DE AMBIGÜEDADES:
           - Si un campo no está claro, razona sobre dónde debería estar
           - Si hay múltiples posibilidades, elige la más probable basándote en el contexto
           - Si no encuentras un campo, indica por qué (borroso, no visible, etc.)
        
        Extrae la siguiente información en formato JSON estricto (responde SOLO con el JSON):
        {
            "cuit_librador": "CUIT del librador normalizado a formato XX-XXXXXXXX-X",
            "banco": "Nombre completo del banco emisor",
            "fecha_emision": "Fecha de emisión en formato YYYY-MM-DD",
            "fecha_pago": "Fecha de pago/vencimiento en formato YYYY-MM-DD",
            "importe": número decimal (extrae del campo numérico, valida con letras si es posible),
            "numero_cheque": "Número único del cheque",
            "cbu_beneficiario": "CBU o CUIT del beneficiario si aparece, sino null o cadena vacía",
            "razonamiento": "Breve explicación de tu análisis, validaciones realizadas y observaciones importantes"
        }
        
        REGLAS ESTRICTAS:
        - Responde ÚNICAMENTE con el JSON válido, sin texto adicional, sin markdown, sin explicaciones fuera del JSON
        - Si un campo no se puede determinar, usa "" para strings o 0 para números
        - El campo "razonamiento" debe ser breve (máximo 200 caracteres)
        - Normaliza todos los formatos (CUIT siempre con guiones, fechas siempre YYYY-MM-DD)
        """
        
        result = await self.process_image(image_data, mime_type, cheque_prompt)
        
        # Try to parse JSON from response with improved extraction
        import json
        import re
        
        try:
            # Improved JSON extraction - handles nested objects and arrays
            text = result.get("extracted_text", "")
            
            # Try to find JSON block (may be wrapped in markdown code blocks)
            json_patterns = [
                r'```json\s*(\{.*?\})\s*```',  # JSON in markdown code block
                r'```\s*(\{.*?\})\s*```',       # JSON in code block
                r'(\{.*\})',                    # Any JSON object
            ]
            
            cheque_data = {}
            for pattern in json_patterns:
                json_match = re.search(pattern, text, re.DOTALL)
                if json_match:
                    try:
                        cheque_data = json.loads(json_match.group(1))
                        break
                    except json.JSONDecodeError:
                        continue
            
            # If no JSON found, try to extract key-value pairs manually
            if not cheque_data:
                logger.warning("Could not find JSON in response, attempting manual extraction")
                # Fallback: try to extract individual fields using regex
                cheque_data = self._extract_fields_fallback(text)
            
            result["cheque_data"] = cheque_data
            logger.info(f"Successfully extracted cheque data: {list(cheque_data.keys())}")
            
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


