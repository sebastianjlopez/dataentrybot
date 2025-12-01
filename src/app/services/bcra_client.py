"""
Client for BCRA (Banco Central de la República Argentina) API.
Handles credit checks and debt verification.
"""
import logging
from typing import Dict, Any, Optional
import aiohttp
import re
from src.app.core.config import settings

logger = logging.getLogger(__name__)


class BCRAClient:
    """Client for BCRA API integration."""
    
    def __init__(self):
        """Initialize BCRA client."""
        self.api_url = settings.bcra_api_url
        self.api_key = settings.bcra_api_key
        self.mock_mode = settings.bcra_mock_mode
        # BCRA API endpoint for rejected cheques
        self.bcra_api_base = "https://api.bcra.gob.ar"
        self.bcra_cheques_endpoint = "/centraldedeudores/v1.0/Deudas/ChequesRechazados"
        logger.info(f"BCRA client initialized (mock_mode={self.mock_mode})")
    
    def _normalize_cuit(self, cuit: str) -> str:
        """
        Normalize CUIT format: remove dashes and spaces, return as integer string.
        
        Args:
            cuit: CUIT in any format (XX-XXXXXXXX-X, XXXXXXXXXXX, etc.)
            
        Returns:
            CUIT as plain digits (XXXXXXXXXXX)
        """
        # Remove dashes, spaces, and any non-digit characters
        cuit_clean = re.sub(r'[^\d]', '', cuit)
        return cuit_clean
    
    async def _call_bcra_api(self, cuit: str) -> Dict[str, Any]:
        """
        Call BCRA API to get rejected cheques data.
        
        Args:
            cuit: CUIT to check (format: XX-XXXXXXXX-X or XXXXXXXXXXX)
            
        Returns:
            Dictionary with API response data
        """
        # Normalize CUIT (remove dashes)
        cuit_normalized = self._normalize_cuit(cuit)
        
        # Build API URL
        url = f"{self.bcra_api_base}{self.bcra_cheques_endpoint}/{cuit_normalized}"
        
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'DataEntryBot/1.0'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 404:
                        # No records found
                        logger.info(f"No rejected cheques found for CUIT {cuit}")
                        return {
                            "status": 0,
                            "results": None
                        }
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"BCRA API returned status {response.status}: {error_text}")
                        raise Exception(f"BCRA API error: HTTP {response.status}")
                    
                    # Parse JSON response
                    data = await response.json()
                    return data
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling BCRA API: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
    
    def _count_rejected_cheques(self, api_response: Dict[str, Any]) -> int:
        """
        Count rejected cheques from BCRA API response.
        
        The API response structure is:
        {
            "status": 0,
            "results": {
                "identificacion": ...,
                "denominacion": ...,
                "causales": [
                    {
                        "causal": "...",
                        "entidades": [
                            {
                                "entidad": ...,
                                "detalle": [
                                    { ... cheque data ... },
                                    ...
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        Args:
            api_response: Response from BCRA API
            
        Returns:
            Total count of rejected cheques
        """
        if not api_response or api_response.get("status") != 0:
            return 0
        
        results = api_response.get("results")
        if not results:
            return 0
        
        causales = results.get("causales", [])
        total_count = 0
        
        # Count cheques in all causales -> entidades -> detalle
        for causal in causales:
            entidades = causal.get("entidades", [])
            for entidad in entidades:
                detalle = entidad.get("detalle", [])
                total_count += len(detalle)
        
        return total_count
    
    def _determine_risk_level(self, cheques_count: int) -> str:
        """
        Determine credit risk level based on rejected cheques count.
        
        Args:
            cheques_count: Number of rejected cheques
            
        Returns:
            Risk level (A, B, or C)
        """
        if cheques_count == 0:
            return "A"
        elif cheques_count < 5:
            return "B"
        else:
            return "C"
    
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
            # Call real BCRA API
            api_response = await self._call_bcra_api(cuit)
            cheques_count = self._count_rejected_cheques(api_response)
            riesgo = self._determine_risk_level(cheques_count)
            
            # Determine status message
            if cheques_count == 0:
                estado = "Sin registros"
            else:
                estado = f"Con {cheques_count} cheque(s) rechazado(s)"
            
            return {
                "estado_bcra": estado,
                "cheques_rechazados": cheques_count,
                "riesgo_crediticio": riesgo,
                "cuit": cuit,
                "mock": False
            }
            
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




