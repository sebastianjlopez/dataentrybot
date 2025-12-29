"""
Client for AFIP Padrón A13 API using AFIP SDK.
Handles taxpayer information queries from AFIP registry.
"""
import logging
import re
from typing import Dict, Any, Optional
import aiohttp
from src.app.core.config import settings

logger = logging.getLogger(__name__)


class AFIPClient:
    """Client for AFIP Padrón A13 API."""
    
    def __init__(self):
        """Initialize AFIP client with configuration."""
        self.api_url = "https://app.afipsdk.com/api/v1/afip/requests"
        self.token = getattr(settings, 'afip_token', None)
        self.sign = getattr(settings, 'afip_sign', None)
        self.cuit_representada = getattr(settings, 'afip_cuit_representada', None)
        self.environment = getattr(settings, 'afip_environment', 'dev')
        
        if not all([self.token, self.sign, self.cuit_representada]):
            logger.warning("AFIP credentials not fully configured. Some features may not work.")
        else:
            logger.info(f"AFIP client initialized (environment={self.environment})")
    
    def _cuit_to_int(self, cuit: str) -> Optional[int]:
        """
        Convert CUIT from format XX-XXXXXXXX-X to integer.
        
        Args:
            cuit: CUIT string in format XX-XXXXXXXX-X or just digits
            
        Returns:
            Integer CUIT or None if invalid
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
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make HTTP request to AFIP SDK API.
        
        Args:
            method: AFIP method name
            params: Method parameters
            
        Returns:
            Response data as dictionary
        """
        if not all([self.token, self.sign, self.cuit_representada]):
            return {
                "error": "AFIP credentials not configured",
                "message": "Please configure AFIP_TOKEN, AFIP_SIGN, and AFIP_CUIT_REPRESENTADA"
            }
        
        payload = {
            "environment": self.environment,
            "method": method,
            "wsid": "ws_sr_padron_a13",
            "params": {
                "token": self.token,
                "sign": self.sign,
                "cuitRepresentada": self.cuit_representada,
                **params
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            # Deshabilitar verificación SSL temporalmente para pruebas locales
            ssl_context = False
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"AFIP API error: Status {response.status}, Response: {error_text}")
                        return {
                            "error": f"HTTP {response.status}",
                            "message": error_text
                        }
        except aiohttp.ClientError as e:
            logger.error(f"AFIP API request error: {str(e)}")
            return {"error": str(e), "message": "Connection error"}
        except Exception as e:
            logger.error(f"Unexpected error in AFIP API request: {str(e)}")
            return {"error": str(e), "message": "Unexpected error"}
    
    async def get_taxpayer_details(self, cuit: str) -> Dict[str, Any]:
        """
        Get taxpayer details from AFIP Padrón A13.
        
        Args:
            cuit: CUIT string in format XX-XXXXXXXX-X
            
        Returns:
            Dictionary with taxpayer information
        """
        identificacion = self._cuit_to_int(cuit)
        if not identificacion:
            return {
                "error": "Invalid CUIT format",
                "message": "CUIT must be in format XX-XXXXXXXX-X or 11 digits"
            }
        
        logger.info(f"Querying AFIP Padrón A13 for CUIT: {cuit} ({identificacion})")
        
        result = await self._make_request("getPersona", {"idPersona": identificacion})
        
        return result
    
    async def get_tax_id_by_document(self, dni: int) -> Dict[str, Any]:
        """
        Get CUIT from DNI.
        
        Args:
            dni: DNI number
            
        Returns:
            Dictionary with CUIT information
        """
        logger.info(f"Querying AFIP for CUIT by DNI: {dni}")
        
        result = await self._make_request("getIdPersonaListByDocumento", {"documento": dni})
        
        return result
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        Get AFIP server status.
        
        Returns:
            Dictionary with server status
        """
        result = await self._make_request("dummy", {})
        return result
    
    def format_taxpayer_info(self, data: Dict[str, Any]) -> str:
        """
        Format taxpayer information for display.
        
        Args:
            data: Raw taxpayer data from AFIP
            
        Returns:
            Formatted string with taxpayer information
        """
        if "error" in data:
            return f"❌ Error: {data.get('message', 'Unknown error')}"
        
        # Extract relevant information
        persona = data.get("persona", {})
        if not persona:
            return "❌ No se encontró información del contribuyente"
        
        # Basic information
        razon_social = persona.get("razonSocial", "N/A")
        tipo_persona = persona.get("tipoPersona", "N/A")
        estado_clave = persona.get("estadoClave", "N/A")
        
        # Address information
        domicilio = persona.get("domicilio", {})
        direccion = domicilio.get("direccion", "N/A") if domicilio else "N/A"
        localidad = domicilio.get("localidad", "N/A") if domicilio else "N/A"
        provincia = domicilio.get("descripcionProvincia", "N/A") if domicilio else "N/A"
        codigo_postal = domicilio.get("codPostal", "N/A") if domicilio else "N/A"
        
        # Tax information
        impuestos = persona.get("impuestos", [])
        condicion_iva = "N/A"
        actividades = []
        
        for impuesto in impuestos:
            id_impuesto = impuesto.get("idImpuesto", "")
            if id_impuesto == "30":  # IVA
                condicion_iva = impuesto.get("descripcionImpuesto", "N/A")
            elif id_impuesto == "32":  # Actividades
                actividades.append(impuesto.get("descripcionImpuesto", ""))
        
        # Format output
        output = f"📋 *PADRÓN A13 - AFIP*\n\n"
        output += f"🏢 *Razón Social:*\n{razon_social}\n\n"
        output += f"👤 *Tipo Persona:* {tipo_persona}\n"
        output += f"📊 *Estado Clave:* {estado_clave}\n\n"
        
        output += f"📍 *Domicilio Fiscal:*\n"
        output += f"{direccion}\n"
        output += f"{localidad}, {provincia}\n"
        output += f"CP: {codigo_postal}\n\n"
        
        output += f"💰 *Condición IVA:*\n{condicion_iva}\n"
        
        if actividades:
            output += f"\n📝 *Actividades:*\n"
            for actividad in actividades[:5]:  # Limit to first 5
                if actividad:
                    output += f"• {actividad}\n"
        
        # Add province alert for Convenio Multilateral
        if provincia and provincia.upper() not in ["N/A", ""]:
            if "CIUDAD AUTONOMA DE BUENOS AIRES" in provincia.upper() or "CABA" in provincia.upper():
                output += f"\n⚠️ *Alerta:* Proveedor de CABA - Verificar Convenio Multilateral\n"
            elif "BUENOS AIRES" in provincia.upper() and "CIUDAD" not in provincia.upper():
                output += f"\n⚠️ *Alerta:* Proveedor de PBA - Verificar Convenio Multilateral\n"
        
        return output


