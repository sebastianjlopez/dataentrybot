"""
Specialized processor for cheque documents.
Handles cheque detection, extraction, and BCRA validation.
"""
import logging
from typing import Dict, Any, Optional, List
from src.app.core.models import ChequeData
from src.app.services.gemini_client import GeminiClient
from src.app.services.bcra_client import BCRAClient
import re

logger = logging.getLogger(__name__)


class ChequesProcessor:
    """Processor for cheque documents."""
    
    def __init__(self):
        """Initialize cheque processor with Gemini and BCRA clients."""
        self.gemini_client = GeminiClient()
        self.bcra_client = BCRAClient()
        logger.info("Cheques processor initialized")
    
    def is_cheque(self, image_data: bytes, filename: Optional[str] = None) -> bool:
        """
        Detect if an image/document is a cheque.
        
        Args:
            image_data: Binary image data
            filename: Optional filename for detection
            
        Returns:
            True if document appears to be a cheque
        """
        # Simple heuristic: check filename or basic image analysis
        if filename:
            filename_lower = filename.lower()
            if "cheque" in filename_lower or "cpd" in filename_lower or "payment" in filename_lower:
                return True
        
        # For PDFs, we'll let Gemini detect if it contains cheques
        # This allows processing documents that may contain cheques
        return False
    
    async def detect_and_process_cheques(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg",
        filename: Optional[str] = None
    ) -> List[ChequeData]:
        """
        Detect if document contains cheques and process all found cheques.
        Uses Gemini to analyze the document content.
        
        Args:
            image_data: Binary image data
            mime_type: MIME type of the image
            filename: Optional filename
            
        Returns:
            List of ChequeData models (empty if no cheques found)
        """
        # Always try to process as cheques - Gemini will determine if there are any
        return await self.process_multiple_cheques(image_data, mime_type)
    
    async def process_multiple_cheques(
        self,
        image_data: bytes,
        mime_type: str = "image/jpeg"
    ) -> List[ChequeData]:
        """
        Process an image that may contain multiple cheques.
        
        Args:
            image_data: Binary image data
            mime_type: MIME type of the image
            
        Returns:
            List of ChequeData models (one per cheque found)
        """
        try:
            logger.info("Processing document for multiple cheques with Gemini...")
            gemini_result = await self.gemini_client.process_cheque(image_data, mime_type)
            
            if not gemini_result.get("success"):
                logger.error("Gemini processing failed")
                return []
            
            cheque_data_raw = gemini_result.get("cheque_data", {})
            
            # Check if we have cheques
            cheques_list = []
            if not cheque_data_raw:
                logger.warning("No cheque data extracted from Gemini response")
                return []
            
            # Extract cheques array
            if "cheques" in cheque_data_raw and isinstance(cheque_data_raw["cheques"], list):
                cheques_raw = cheque_data_raw["cheques"]
            elif isinstance(cheque_data_raw, list):
                cheques_raw = cheque_data_raw
            elif isinstance(cheque_data_raw, dict):
                # Single cheque object, wrap in list
                cheques_raw = [cheque_data_raw]
            else:
                logger.warning(f"Unexpected cheque_data format: {type(cheque_data_raw)}")
                return []
            
            if not cheques_raw or len(cheques_raw) == 0:
                logger.warning("No cheques found in extracted data")
                return []
            
            logger.info(f"Found {len(cheques_raw)} cheque(s) in document")
            
            # Process each cheque
            for idx, cheque_raw in enumerate(cheques_raw):
                try:
                    # Normalize and validate data (handle None values)
                    cuit_librador = self._normalize_cuit(cheque_raw.get("cuit_librador") or "")
                    banco = (cheque_raw.get("banco") or "").strip() if cheque_raw.get("banco") else ""
                    fecha_emision = (cheque_raw.get("fecha_emision") or "").strip() if cheque_raw.get("fecha_emision") else ""
                    fecha_pago = (cheque_raw.get("fecha_pago") or "").strip() if cheque_raw.get("fecha_pago") else ""
                    importe = self._parse_importe(cheque_raw.get("importe", 0))
                    numero_cheque = str(cheque_raw.get("numero_cheque") or "").strip() if cheque_raw.get("numero_cheque") else ""
                    cbu_benef = cheque_raw.get("cbu_beneficiario")
                    cbu_beneficiario = (cbu_benef.strip() if cbu_benef and isinstance(cbu_benef, str) else None) if cbu_benef else None
                    
                    # Check BCRA status if CUIT is available
                    estado_bcra = ""
                    cheques_rechazados = 0
                    riesgo_crediticio = ""
                    
                    if cuit_librador:
                        logger.info(f"Checking BCRA status for CUIT {idx+1}/{len(cheques_raw)}: {cuit_librador}")
                        bcra_status = await self.bcra_client.check_credit_status(cuit_librador)
                        estado_bcra = bcra_status.get("estado_bcra", "")
                        cheques_rechazados = bcra_status.get("cheques_rechazados", 0)
                        riesgo_crediticio = bcra_status.get("riesgo_crediticio", "")
                    
                    # Build ChequeData model
                    cheque_data = ChequeData(
                        tipo_documento="cheque",
                        cuit_librador=cuit_librador,
                        banco=banco,
                        fecha_emision=fecha_emision,
                        fecha_pago=fecha_pago,
                        importe=importe,
                        numero_cheque=numero_cheque,
                        cbu_beneficiario=cbu_beneficiario,
                        estado_bcra=estado_bcra,
                        cheques_rechazados=cheques_rechazados,
                        riesgo_crediticio=riesgo_crediticio
                    )
                    
                    cheques_list.append(cheque_data)
                    logger.info(f"Cheque {idx+1} processed: CUIT={cuit_librador}, Importe={importe}")
                    
                except Exception as e:
                    logger.error(f"Error processing cheque {idx+1}: {str(e)}")
                    continue
            
            logger.info(f"Successfully processed {len(cheques_list)} cheque(s)")
            return cheques_list
            
        except Exception as e:
            logger.error(f"Error processing multiple cheques: {str(e)}")
            return []
    
    async def process_cheque(
        self, 
        image_data: bytes, 
        mime_type: str = "image/jpeg"
    ) -> ChequeData:
        """
        Process a cheque image and extract all relevant data.
        
        Args:
            image_data: Binary image data
            mime_type: MIME type of the image
            
        Returns:
            ChequeData model with extracted information
        """
        try:
            # Step 1: Extract data using Gemini
            logger.info("Processing cheque with Gemini...")
            gemini_result = await self.gemini_client.process_cheque(image_data, mime_type)
            
            if not gemini_result.get("success"):
                logger.error("Gemini processing failed")
                return ChequeData()
            
            # Step 2: Parse extracted data
            cheque_data_raw = gemini_result.get("cheque_data", {})
            
            # Step 3: Normalize and validate data
            cuit_librador = self._normalize_cuit(cheque_data_raw.get("cuit_librador", ""))
            banco = cheque_data_raw.get("banco", "").strip()
            fecha_emision = cheque_data_raw.get("fecha_emision", "").strip()
            fecha_pago = cheque_data_raw.get("fecha_pago", "").strip()
            importe = self._parse_importe(cheque_data_raw.get("importe", 0))
            numero_cheque = str(cheque_data_raw.get("numero_cheque", "")).strip()
            cbu_beneficiario = cheque_data_raw.get("cbu_beneficiario", "").strip() or None
            
            # Step 4: Check BCRA status if CUIT is available
            estado_bcra = ""
            cheques_rechazados = 0
            riesgo_crediticio = ""
            
            if cuit_librador:
                logger.info(f"Checking BCRA status for CUIT: {cuit_librador}")
                bcra_status = await self.bcra_client.check_credit_status(cuit_librador)
                estado_bcra = bcra_status.get("estado_bcra", "")
                cheques_rechazados = bcra_status.get("cheques_rechazados", 0)
                riesgo_crediticio = bcra_status.get("riesgo_crediticio", "")
            
            # Step 5: Build ChequeData model
            cheque_data = ChequeData(
                tipo_documento="cheque",
                cuit_librador=cuit_librador,
                banco=banco,
                fecha_emision=fecha_emision,
                fecha_pago=fecha_pago,
                importe=importe,
                numero_cheque=numero_cheque,
                cbu_beneficiario=cbu_beneficiario,
                estado_bcra=estado_bcra,
                cheques_rechazados=cheques_rechazados,
                riesgo_crediticio=riesgo_crediticio
            )
            
            logger.info(f"Cheque processed successfully. CUIT: {cuit_librador}, Importe: {importe}")
            return cheque_data
            
        except Exception as e:
            logger.error(f"Error processing cheque: {str(e)}")
            return ChequeData()
    
    def _normalize_cuit(self, cuit: str) -> str:
        """
        Normalize CUIT format to XX-XXXXXXXX-X.
        
        Args:
            cuit: CUIT string in various formats
            
        Returns:
            Normalized CUIT string
        """
        if not cuit:
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', cuit)
        
        # Format as XX-XXXXXXXX-X
        if len(digits) == 11:
            return f"{digits[:2]}-{digits[2:10]}-{digits[10]}"
        
        return cuit
    
    def _parse_importe(self, importe: Any) -> float:
        """
        Parse importe from various formats to float.
        
        Args:
            importe: Importe in various formats (string, number, etc.)
            
        Returns:
            Float value of importe
        """
        if isinstance(importe, (int, float)):
            return float(importe)
        
        if isinstance(importe, str):
            # Remove currency symbols and spaces
            importe_clean = re.sub(r'[^\d.,]', '', importe)
            # Replace comma with dot for decimal
            importe_clean = importe_clean.replace(',', '.')
            try:
                return float(importe_clean)
            except ValueError:
                return 0.0
        
        return 0.0


