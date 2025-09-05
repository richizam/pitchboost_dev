from pydantic import BaseModel, AnyHttpUrl
from typing import Literal, List
from app.schemas.common import Scores

Scenario = Literal["investor", "client", "academic"]

class AnalyzeRequest(BaseModel):
    user_id: str
    scenario: Scenario = "investor"
    audio_url: AnyHttpUrl

class AnalyzeResponse(BaseModel):
    scores: Scores
    strengths: List[str]
    improvements: List[str]
    rewritten_pitch_60s: str
