"""
Pydantic models for data validation and serialization.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ChequeData(BaseModel):
    """Model for cheque data extracted from OCR."""
    tipo_documento: str = "cheque"
    cuit_librador: str = Field(default="", description="CUIT del librador del cheque")
    banco: str = Field(default="", description="Banco emisor del cheque")
    fecha_emision: str = Field(default="", description="Fecha de emisión del cheque")
    fecha_pago: str = Field(default="", description="Fecha de pago del cheque")
    importe: float = Field(default=0.0, description="Importe del cheque")
    numero_cheque: str = Field(default="", description="Número de cheque")
    cbu_beneficiario: Optional[str] = Field(default=None, description="CBU o CUIT del beneficiario")
    estado_bcra: str = Field(default="", description="Estado crediticio según BCRA")
    cheques_rechazados: int = Field(default=0, description="Cantidad de cheques rechazados")
    riesgo_crediticio: str = Field(default="", description="Nivel de riesgo crediticio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tipo_documento": "cheque",
                "cuit_librador": "20-12345678-9",
                "banco": "Banco Nación",
                "fecha_emision": "2024-01-15",
                "fecha_pago": "2024-01-30",
                "importe": 50000.0,
                "numero_cheque": "12345678",
                "cbu_beneficiario": "1234567890123456789012",
                "estado_bcra": "Sin deuda",
                "cheques_rechazados": 0,
                "riesgo_crediticio": "A"
            }
        }


class DocumentData(BaseModel):
    """Model for general document data extracted from OCR."""
    tipo_documento: str = Field(default="documento", description="Tipo de documento")
    contenido: str = Field(default="", description="Contenido extraído del documento")
    datos_estructurados: Dict[str, Any] = Field(default_factory=dict, description="Datos estructurados extraídos")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos del documento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tipo_documento": "documento",
                "contenido": "Texto extraído del documento...",
                "datos_estructurados": {},
                "metadata": {}
            }
        }


class ProcessRequest(BaseModel):
    """Model for processing validated data from Mini App."""
    tipo_documento: str
    datos: Dict[str, Any]
    usuario_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "tipo_documento": "cheque",
                "datos": {
                    "cuit_librador": "20-12345678-9",
                    "banco": "Banco Nación",
                    "importe": 50000.0
                },
                "usuario_id": "123456789",
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class ProcessResponse(BaseModel):
    """Response model for processing endpoint."""
    success: bool
    message: str
    data_id: Optional[str] = None


