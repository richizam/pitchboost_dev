from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud
from app.core.config import settings

router = APIRouter(prefix="/v1", tags=["users"])


@router.get("/credits/{tg_user_id}")
async def get_credits(tg_user_id: str, db: Session = Depends(get_db)):
    user = crud.get_or_create_user(db, tg_user_id)
    free_limit = settings.FREE_CREDITS
    free_remaining = max(0, free_limit - user.credits_free_used)
    total_remaining = free_remaining + user.credits_paid
    return {
        "free_used": user.credits_free_used,
        "free_limit": free_limit,
        "paid": user.credits_paid,
        "total_remaining": total_remaining,
    }


@router.post("/pay")
async def mock_pay(body: dict, db: Session = Depends(get_db)):
    tg_user_id = body.get("tg_user_id")
    amount = int(body.get("amount", 0))
    if not tg_user_id or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid payment request")
    user = crud.get_or_create_user(db, tg_user_id)
    crud.add_paid_credits(db, user, amount)
    return {"status": "ok", "paid": user.credits_paid}


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
