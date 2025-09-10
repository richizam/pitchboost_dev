# analyze.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.analyze import AnalyzeRequest, AnalyzeAckResponse
from app.services.storage import storage
from app.services.kafka_client import kafka_producer
from app.core.logging import logger
from app.core.config import settings
from app.db.database import get_db
from app.db import crud

router = APIRouter(prefix="/v1", tags=["analyze"])


@router.post(
    "/analyze", response_model=AnalyzeAckResponse, status_code=status.HTTP_202_ACCEPTED
)
async def analyze(
    req: AnalyzeRequest, db: Session = Depends(get_db)
) -> AnalyzeAckResponse:
    """
    1) Descarga el audio desde la URL recibida (Telegram).
    2) Sube a S3 con clave {ENV}/{uuid}.{ext}.
    3) Publica en Kafka (topic processing) {user_id, audio_id, request_message, scenario, duration_minutes}.
    4) Devuelve ACK con audio_key.
    """
    # Find or create user
    user = crud.get_or_create_user(db, req.user_id)

    # Optional duration check if Telegram provided duration
    if (
        req.media_duration_sec is not None
        and req.media_duration_sec > settings.AUDIO_MAX_SECONDS
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Audio too long (>{settings.AUDIO_MAX_SECONDS}s)",
        )

    # Attempts gating
    if user.attempts > 0:
        crud.use_attempt(db, user)
    else:
        raise HTTPException(status_code=402, detail="No attempts remaining")

    audio_url_str = str(req.audio_url)

    # 1-2) Subir a S3
    try:
        uploaded = await storage.upload_audio_from_url(
            url=audio_url_str, user_id=req.user_id
        )
        key = uploaded["key"]
        logger.info(f"S3 ok bucket={uploaded['bucket']} key={key}")
    except HTTPException:
        raise
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
        crud.create_pitch(
            db,
            user_id=user.id,
            audio_key=key,
            scenario=req.scenario,
            duration_minutes=req.duration_minutes,
            status="queued",
        )
        return AnalyzeAckResponse(status="queued", audio_key=key)
    except Exception as e:
        logger.exception("Kafka produce failed")
        raise HTTPException(status_code=502, detail=f"Kafka produce failed: {e}")
