# analyze.py
from fastapi import APIRouter, HTTPException, status
from app.schemas.analyze import AnalyzeRequest, AnalyzeAckResponse
from app.services.storage import storage
from app.services.kafka_client import kafka_producer
from app.core.logging import logger

router = APIRouter(prefix="/v1", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeAckResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze(req: AnalyzeRequest) -> AnalyzeAckResponse:
    """
    1) Descarga el audio desde la URL recibida (Telegram).
    2) Sube a S3 con clave {ENV}/{uuid}.{ext}.
    3) Publica en Kafka (topic processing) {user_id, audio_id, request_message, scenario, duration_minutes}.
    4) Devuelve ACK con audio_key.
    """
    audio_url_str = str(req.audio_url)

    # 1-2) Subir a S3
    try:
        uploaded = await storage.upload_audio_from_url(url=audio_url_str, user_id=req.user_id)
        key = uploaded["key"]
        logger.info(f"S3 ok bucket={uploaded['bucket']} key={key}")
    except Exception as e:
        logger.exception("S3 upload failed")
        raise HTTPException(status_code=502, detail=f"S3 upload failed: {e}")

    # 3) Enviar a Kafka
    try:
        payload = {
            "user_id": req.user_id,
            "audio_id": key,
            "request_message": "",
            "scenario": req.scenario,
            "duration_minutes": req.duration_minutes,
        }
        kafka_producer.enqueue_for_processing(payload)
        kafka_producer.flush()
        return AnalyzeAckResponse(status="queued", audio_key=key)
    except Exception as e:
        logger.exception("Kafka produce failed")
        raise HTTPException(status_code=502, detail=f"Kafka produce failed: {e}")
