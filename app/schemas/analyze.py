# analyze.py
from pydantic import BaseModel, AnyHttpUrl, Field
from typing import Literal, Optional

Scenario = Literal["investor", "client", "academic"]
DurationMinutes = Literal[1, 3, 5]


class AnalyzeRequest(BaseModel):
    user_id: str
    scenario: Scenario = "investor"
    duration_minutes: DurationMinutes = 1
    audio_url: AnyHttpUrl
    media_duration_sec: Optional[int] = Field(default=None, ge=0)


class AnalyzeAckResponse(BaseModel):
    status: str  # siempre "queued"
    audio_key: str
