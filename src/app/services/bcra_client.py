"""
Client for BCRA (Banco Central de la República Argentina) API.
Handles credit checks and debt verification.
"""
import logging
from typing import Dict, Any, Optional
import aiohttp
import re
# Removed settings import - no longer using mock mode

logger = logging.getLogger(__name__)


class BCRAClient:
    """Client for BCRA API integration."""
    
    def __init__(self):
        """Initialize BCRA client."""
        # BCRA API endpoint for rejected cheques
        self.bcra_api_base = "https://api.bcra.gob.ar"
        self.bcra_cheques_endpoint = "/centraldedeudores/v1.0/Deudas/ChequesRechazados"
        logger.info("BCRA client initialized - Using official BCRA API")
    
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
                    logger.debug(f"BCRA API response for CUIT {cuit}: status={data.get('status')}, has_results={bool(data.get('results'))}")
                    if data.get("results"):
                        logger.debug(f"Response structure: causales={len(data['results'].get('causales', []))}")
                    return data
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling BCRA API: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
    
    def _count_rejected_cheques(self, api_response: Dict[str, Any]) -> int:
        """
        Count rejected cheques from BCRA API response.
        
        IMPORTANT: Only counts cheques that are NOT cancelled (fechaPago is null/empty).
        This matches the behavior of the BCRA website which only shows active rejected cheques.
        
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
                                    {
                                        "nroCheque": ...,
                                        "fechaRechazo": "...",
                                        "monto": ...,
                                        "fechaPago": "..." or null,  // null = not cancelled
                                        "fechaPagoMulta": "...",
                                        "estadoMulta": "...",
                                        ...
                                    },
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
            Total count of active (non-cancelled) rejected cheques
        """
        if not api_response or api_response.get("status") != 0:
            logger.debug("API response has no status or status != 0")
            return 0
        
        results = api_response.get("results")
        if not results:
            logger.debug("API response has no results")
            return 0
        
        causales = results.get("causales", [])
        total_count = 0
        total_cheques = 0  # Total including cancelled
        cancelled_count = 0  # Count of cancelled cheques
        
        # Count only active (non-cancelled) cheques
        # A cheque is considered cancelled if fechaPago is not null/empty
        for causal in causales:
            causal_name = causal.get("causal", "N/A")
            entidades = causal.get("entidades", [])
            
            for entidad in entidades:
                detalle = entidad.get("detalle", [])
                total_cheques += len(detalle)
                
                for cheque in detalle:
                    fecha_pago = cheque.get("fechaPago")
                    # Cheque is active (not cancelled) if fechaPago is null, empty, or None
                    if not fecha_pago or fecha_pago == "":
                        total_count += 1
                    else:
                        cancelled_count += 1
                        logger.debug(f"Excluding cancelled cheque: fechaPago={fecha_pago}")
        
        if total_cheques > 0:
            logger.info(f"Cheques rechazados: {total_count} activos, {cancelled_count} cancelados (total: {total_cheques})")
        elif total_cheques == 0 and api_response.get("results"):
            logger.info("No cheques found in API response (results exists but causales is empty)")
        else:
            logger.info("No cheques found - API returned no results")
        
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
        Check credit status for a given CUIT using the official BCRA API.
        
        Args:
            cuit: CUIT to check (format: XX-XXXXXXXX-X)
            
        Returns:
            Dictionary with credit status information
        """
        try:
            logger.info(f"Checking BCRA status for CUIT: {cuit}")
            # Call real BCRA API
            api_response = await self._call_bcra_api(cuit)
            cheques_count = self._count_rejected_cheques(api_response)
            riesgo = self._determine_risk_level(cheques_count)
            
            # Determine status message
            if cheques_count == 0:
                estado = "Sin registros"
            else:
                estado = f"Con {cheques_count} cheque(s) rechazado(s)"
            
            logger.info(f"BCRA status for CUIT {cuit}: {cheques_count} cheques rechazados, riesgo {riesgo}")
            
            return {
                "estado_bcra": estado,
                "cheques_rechazados": cheques_count,
                "riesgo_crediticio": riesgo,
                "cuit": cuit
            }
            
        except Exception as e:
            logger.error(f"Error checking BCRA credit status for CUIT {cuit}: {str(e)}")
            return {
                "estado_bcra": "Error",
                "cheques_rechazados": 0,
                "riesgo_crediticio": "N/A",
                "error": str(e)
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




