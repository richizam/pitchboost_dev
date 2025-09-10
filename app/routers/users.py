# app/routers/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud

router = APIRouter(prefix="/v1", tags=["users"])


@router.get("/balance/{tg_user_id}")
async def balance(tg_user_id: str, db: Session = Depends(get_db)):
    user = crud.get_or_create_user(db, tg_user_id)
    return {"telegram_id": tg_user_id, "attempts": user.attempts}


@router.get("/history/{tg_user_id}")
async def history(tg_user_id: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_tg_id(db, tg_user_id)
    if not user:
        return []
    pitches = crud.list_pitches(db, user.id)
    return [
        {
            "audio_key": p.audio_key,
            "scenario": p.scenario,
            "duration_minutes": p.duration_minutes,
            "status": p.status,
            "created_at": p.created_at,
        }
        for p in pitches
    ]
