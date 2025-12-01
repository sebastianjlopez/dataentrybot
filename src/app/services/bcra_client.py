"""
Client for BCRA (Banco Central de la República Argentina) API.
Handles credit status checks, debt queries, and rejected cheques.
"""
import logging
import re
from typing import Dict, Any, Optional, List
import aiohttp
from src.app.core.config import settings

logger = logging.getLogger(__name__)


class BCRAClient:
    """Client for BCRA Central de Deudores API."""
    
    def __init__(self):
        """Initialize BCRA client with configuration."""
        self.base_url = settings.bcra_api_url.rstrip('/')
        logger.info(f"BCRA client initialized (base_url={self.base_url})")
    
    def _cuit_to_identificacion(self, cuit: str) -> Optional[int]:
        """
        Convert CUIT from format XX-XXXXXXXX-X to integer (just digits).
        
        Args:
            cuit: CUIT string in format XX-XXXXXXXX-X or just digits
            
        Returns:
            Integer identification or None if invalid
        """
        if not cuit:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', cuit)
        
        if len(digits) == 11:
            try:
                return int(digits)
            except ValueError:
                return None
        
        return None
    
    async def _make_request(
        self, 
        endpoint: str, 
        identificacion: int
    ) -> Dict[str, Any]:
        """
        Make HTTP request to BCRA API.
        
        Args:
            endpoint: API endpoint path
            identificacion: Identification number (CUIT as integer)
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}{endpoint.format(Identificacion=identificacion)}"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            # Deshabilitar verificación SSL temporalmente para pruebas locales
            ssl_context = False  # Deshabilita verificación SSL
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        # La API puede retornar status 200 (HTTP) con diferentes formatos JSON
                        # Normalizar a formato esperado: {"status": 0, "results": {...}}
                        if isinstance(data, dict):
                            # Si ya tiene "status" y "results", retornarlo tal cual
                            if "status" in data and "results" in data:
                                # Si status es 200 (HTTP code), cambiarlo a 0 (success)
                                if data.get("status") == 200:
                                    data["status"] = 0
                                return data
                            # Si tiene "results" pero no "status", agregar status: 0
                            elif "results" in data:
                                return {"status": 0, "results": data["results"]}
                            # Si es un dict sin estructura conocida, envolverlo
                            else:
                                return {"status": 0, "results": data}
                        # Si no es dict, envolverlo
                        return {"status": 0, "results": {}}
                    elif response.status == 404:
                        logger.warning(f"BCRA API: No data found for identificacion {identificacion}")
                        return {"status": 0, "results": {}}
                    elif response.status == 400:
                        error_data = await response.json()
                        logger.error(f"BCRA API Bad Request: {error_data}")
                        return {"status": -1, "errorMessages": error_data.get("errorMessages", [])}
                    else:
                        logger.error(f"BCRA API error: Status {response.status}")
                        return {"status": -1, "error": f"HTTP {response.status}"}
        except aiohttp.ClientError as e:
            logger.error(f"BCRA API request error: {str(e)}")
            return {"status": -1, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in BCRA API request: {str(e)}")
            return {"status": -1, "error": str(e)}
    
    async def get_deudas(self, cuit: str) -> Dict[str, Any]:
        """
        Get current debts for a CUIT.
        
        Args:
            cuit: CUIT string in format XX-XXXXXXXX-X
            
        Returns:
            Dictionary with debt information
        """
        identificacion = self._cuit_to_identificacion(cuit)
        if not identificacion:
            return {"status": -1, "error": "Invalid CUIT format"}
        
        endpoint = "/centraldedeudores/v1.0/Deudas/{Identificacion}"
        return await self._make_request(endpoint, identificacion)
    
    async def get_cheques_rechazados(self, cuit: str) -> Dict[str, Any]:
        """
        Get rejected cheques for a CUIT.
        
        Args:
            cuit: CUIT string in format XX-XXXXXXXX-X
            
        Returns:
            Dictionary with rejected cheques information
        """
        identificacion = self._cuit_to_identificacion(cuit)
        if not identificacion:
            return {"status": -1, "error": "Invalid CUIT format"}
        
        endpoint = "/centraldedeudores/v1.0/Deudas/ChequesRechazados/{Identificacion}"
        return await self._make_request(endpoint, identificacion)
    
    async def get_deudas_historicas(self, cuit: str) -> Dict[str, Any]:
        """
        Get historical debts for a CUIT.
        
        Args:
            cuit: CUIT string in format XX-XXXXXXXX-X
            
        Returns:
            Dictionary with historical debt information
        """
        identificacion = self._cuit_to_identificacion(cuit)
        if not identificacion:
            return {"status": -1, "error": "Invalid CUIT format"}
        
        endpoint = "/centraldedeudores/v1.0/Deudas/Historicas/{Identificacion}"
        return await self._make_request(endpoint, identificacion)
    
    async def check_credit_status(self, cuit: str) -> Dict[str, Any]:
        """
        Check credit status for a CUIT by consolidating information from multiple endpoints.
        
        Args:
            cuit: CUIT string in format XX-XXXXXXXX-X
            
        Returns:
            Dictionary with:
            - estado_bcra: Credit status description
            - cheques_rechazados: Number of rejected cheques
            - riesgo_crediticio: Risk level (A, B, C, etc.)
            - detalles: Additional details
        """
        logger.info(f"Checking credit status for CUIT: {cuit}")
        
        # Get all relevant information
        deudas_data = await self.get_deudas(cuit)
        cheques_data = await self.get_cheques_rechazados(cuit)
        
        # Log raw responses for debugging
        logger.debug(f"BCRA deudas_data status: {deudas_data.get('status')}, has results: {'results' in deudas_data}")
        logger.debug(f"BCRA cheques_data status: {cheques_data.get('status')}, has results: {'results' in cheques_data}")
        
        # Initialize response
        response = {
            "estado_bcra": "",
            "cheques_rechazados": 0,
            "riesgo_crediticio": "",
            "detalles": {}
        }
        
        # Process rejected cheques
        cheques_rechazados = 0
        if cheques_data.get("status") == 0 and "results" in cheques_data:
            results = cheques_data["results"]
            # Count all rejected cheques across all causales and entidades
            if "causales" in results:
                for causal in results["causales"]:
                    if "entidades" in causal:
                        for entidad in causal["entidades"]:
                            if "detalle" in entidad:
                                cheques_rechazados += len(entidad["detalle"])
        
        response["cheques_rechazados"] = cheques_rechazados
        
        # Process current debts
        tiene_deuda = False
        monto_total = 0.0
        situaciones = []
        datos_disponibles = False
        
        # Check if we have valid data (status 0 or 200 both mean success)
        status_code = deudas_data.get("status")
        if status_code == 0 or status_code == 200:
            if "results" in deudas_data:
                results = deudas_data["results"]
                # Check if results is not empty
                if results and (results.get("periodos") or results.get("identificacion")):
                    datos_disponibles = True
                    if "periodos" in results and results["periodos"]:
                        for periodo in results["periodos"]:
                            if "entidades" in periodo:
                                for entidad in periodo["entidades"]:
                                    situacion = entidad.get("situacion", 0)
                                    monto = entidad.get("monto", 0.0)
                                    
                                    if situacion > 0:  # Situación > 0 indicates debt
                                        tiene_deuda = True
                                        monto_total += float(monto)
                                        situaciones.append(situacion)
        
        # If there was an error, log it
        if deudas_data.get("status") == -1:
            logger.warning(f"Error querying BCRA deudas: {deudas_data.get('error', 'Unknown error')}")
        
        # Determine credit status
        if not datos_disponibles and deudas_data.get("status") != -1:
            # No data available from API (empty response)
            response["estado_bcra"] = "Sin datos disponibles en BCRA"
            response["riesgo_crediticio"] = "N/A"
        elif tiene_deuda:
            if monto_total > 0:
                response["estado_bcra"] = f"Con deuda - Monto: ${monto_total:,.2f}"
            else:
                response["estado_bcra"] = "Con deuda registrada"
            
            # Determine risk level based on situation codes and amount
            max_situacion = max(situaciones) if situaciones else 0
            if max_situacion >= 5 or monto_total > 1000000:
                response["riesgo_crediticio"] = "C"
            elif max_situacion >= 3 or monto_total > 500000:
                response["riesgo_crediticio"] = "B"
            else:
                response["riesgo_crediticio"] = "B-"
        else:
            # datos_disponibles is True but no debt found
            if cheques_rechazados > 0:
                response["estado_bcra"] = f"Sin deuda actual, pero con {cheques_rechazados} cheque(s) rechazado(s)"
                response["riesgo_crediticio"] = "B-"
            else:
                response["estado_bcra"] = "Sin deuda"
                response["riesgo_crediticio"] = "A"
        
        # Add details
        response["detalles"] = {
            "monto_total": monto_total,
            "situaciones": situaciones,
            "tiene_deuda_actual": tiene_deuda,
            "datos_disponibles": datos_disponibles,
            "error": deudas_data.get("error") if deudas_data.get("status") == -1 else None
        }
        
        logger.info(f"Credit status for {cuit}: {response['estado_bcra']}, Riesgo: {response['riesgo_crediticio']}")
        
        return response
