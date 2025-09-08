from fastapi import APIRouter, HTTPException
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.storage import storage
from app.services.analyzer_client import analyzer_client
from app.core.logging import logger

router = APIRouter(prefix="/v1", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """
    1) Descarga el audio desde Telegram (o URL recibida).
    2) Sube a Object Storage con clave {env}/{uuid}.{ext} y metadata.
    3) Genera un presigned URL y llama al analizador.
    """
    # Convertir AnyHttpUrl -> str para httpx
    audio_url_str = str(req.audio_url)

    # 1) Subir a S3
    try:
        uploaded = await storage.upload_audio_from_url(url=audio_url_str, user_id=req.user_id)
        key = uploaded["key"]
        presigned = storage.presign_get(key)
        logger.info(
            f"S3 ok bucket={uploaded['bucket']} key={key} size={uploaded['size']} ctype={uploaded['content_type']}"
        )
    except Exception as e:
        logger.exception("S3 upload failed")
        raise HTTPException(status_code=502, detail=f"S3 upload failed: {e}")

    # 2) Llamar al analizador
    try:
        resp = await analyzer_client.analyze(
            user_id=req.user_id,
            scenario=req.scenario,
            audio_url=presigned,
        )
        return resp
    except Exception as e:
        logger.exception("Analyzer failed")
        raise HTTPException(status_code=502, detail=f"Analyzer failed: {e}")
