"""
FastAPI routes for the Data Entry Bot API.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import logging
from src.app.core.models import ChequeData, DocumentData, ProcessRequest, ProcessResponse
from src.app.services.cheques_processor import ChequesProcessor
from src.app.services.gemini_client import GeminiClient
from src.app.utils.file import get_file_mime_type

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize processors
cheques_processor = ChequesProcessor()
gemini_client = GeminiClient()


@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a file (image, PDF, or cheque).
    
    Detects if the file is a cheque and processes it accordingly.
    Returns structured data extracted from the document.
    """
    try:
        # Read file data
        file_data = await file.read()
        filename = file.filename or "uploaded_file"
        mime_type = get_file_mime_type(filename)
        
        logger.info(f"Processing upload: {filename} ({mime_type})")
        
        # Process file directly from memory (no need to save to disk)
        # This works better in cloud environments like Render where filesystem is ephemeral
        
        # Always try to detect cheques first (Gemini will determine if there are any)
        logger.info("Attempting to detect cheques in document...")
        cheques_list = await cheques_processor.detect_and_process_cheques(file_data, mime_type, filename)
        
        if cheques_list and len(cheques_list) > 0:
            # Found cheques - return them
            logger.info(f"Found {len(cheques_list)} cheque(s)")
            return {
                "success": True,
                "tipo_documento": "cheques",
                "cantidad": len(cheques_list),
                "data": [cheque.model_dump() for cheque in cheques_list],
                "filename": filename
            }
        else:
            # Process as general document
            logger.info("Processing as general document...")
            result = await gemini_client.process_image(file_data, mime_type)
            
            document_data = DocumentData(
                tipo_documento="documento",
                contenido=result.get("extracted_text", ""),
                datos_estructurados={},
                metadata={
                    "filename": filename,
                    "mime_type": mime_type
                }
            )
            
            return {
                "success": result.get("success", False),
                "tipo_documento": "documento",
                "data": document_data.model_dump(),
                "filename": filename
            }
            
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/process", response_model=ProcessResponse)
async def process_data(request: ProcessRequest):
    """
    Process validated data from Mini App.
    
    This endpoint receives the edited/validated data from the Mini App
    and performs the final processing (mock for now).
    """
    try:
        logger.info(f"Processing data: tipo={request.tipo_documento}, usuario={request.usuario_id}")
        
        # Mock processing logic
        # In production, this would:
        # - Save to database
        # - Send to external systems
        # - Generate reports
        # - etc.
        
        data_id = f"proc_{request.tipo_documento}_{request.usuario_id or 'unknown'}"
        
        logger.info(f"Data processed successfully: {data_id}")
        
        return ProcessResponse(
            success=True,
            message=f"Datos de {request.tipo_documento} procesados correctamente",
            data_id=data_id
        )
        
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": "data-entry-bot-api",
        "version": "1.0.0"
    }


@router.get("/webapp")
async def webapp():
    """
    Serve the Mini App HTML.
    """
    try:
        from pathlib import Path
        webapp_path = Path("webapp") / "index.html"
        
        if webapp_path.exists():
            return FileResponse(webapp_path)
        else:
            return HTMLResponse(
                content="<h1>Mini App not found</h1>",
                status_code=404
            )
    except Exception as e:
        logger.error(f"Error serving webapp: {str(e)}")
        raise HTTPException(status_code=500, detail="Error serving webapp")


