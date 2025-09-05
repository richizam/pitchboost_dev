from fastapi import APIRouter
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.storage import storage
from app.services.analyzer_client import analyzer_client
from app.core.logging import logger

router = APIRouter(prefix="/v1", tags=["analyze"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    audio_url = await storage.resolve_audio_url(req.audio_url)
    logger.info(f"Analyze request from {req.user_id}, scenario={req.scenario}, url={audio_url}")
    resp = await analyzer_client.analyze(
        user_id=req.user_id, scenario=req.scenario, audio_url=audio_url
    )
    return resp
