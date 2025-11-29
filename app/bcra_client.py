"""
Client for BCRA (Banco Central de la República Argentina) API.
Handles credit checks and debt verification.
"""
import logging
from typing import Dict, Any, Optional
import aiohttp
from app.config import settings

logger = logging.getLogger(__name__)


class BCRAClient:
    """Client for BCRA API integration."""
    
    def __init__(self):
        """Initialize BCRA client."""
        self.api_url = settings.bcra_api_url
        self.api_key = settings.bcra_api_key
        self.mock_mode = settings.bcra_mock_mode
        logger.info(f"BCRA client initialized (mock_mode={self.mock_mode})")
    
    async def check_credit_status(self, cuit: str) -> Dict[str, Any]:
        """
        Check credit status for a given CUIT.
        
        Args:
            cuit: CUIT to check (format: XX-XXXXXXXX-X)
            
        Returns:
            Dictionary with credit status information
        """
        if self.mock_mode:
            return self._mock_credit_check(cuit)
        
        try:
            # Real BCRA API call would go here
            # For now, return mock data
            return self._mock_credit_check(cuit)
            
        except Exception as e:
            logger.error(f"Error checking BCRA credit status: {str(e)}")
            return {
                "estado_bcra": "Error",
                "cheques_rechazados": 0,
                "riesgo_crediticio": "N/A",
                "error": str(e)
            }
    
    def _mock_credit_check(self, cuit: str) -> Dict[str, Any]:
        """
        Mock credit check response.
        In production, this would call the real BCRA API.
        
        Args:
            cuit: CUIT to check
            
        Returns:
            Mock credit status data
        """
        # Simple mock logic: check last digit of CUIT
        # This is just for demo purposes
        last_digit = cuit.split("-")[-1] if "-" in cuit else cuit[-1]
        
        # Mock: if last digit is 0-3, no debt; 4-6, some debt; 7-9, high risk
        last_digit_int = int(last_digit) if last_digit.isdigit() else 0
        
        if last_digit_int <= 3:
            estado = "Sin deuda"
            riesgo = "A"
            rechazados = 0
        elif last_digit_int <= 6:
            estado = "Deuda moderada"
            riesgo = "B"
            rechazados = 1
        else:
            estado = "Deuda alta"
            riesgo = "C"
            rechazados = 3
        
        return {
            "estado_bcra": estado,
            "cheques_rechazados": rechazados,
            "riesgo_crediticio": riesgo,
            "cuit": cuit,
            "mock": True
        }
    
    async def check_rejected_cheques(self, cuit: str) -> int:
        """
        Check number of rejected cheques for a CUIT.
        
        Args:
            cuit: CUIT to check
            
        Returns:
            Number of rejected cheques
        """
        credit_status = await self.check_credit_status(cuit)
        return credit_status.get("cheques_rechazados", 0)

