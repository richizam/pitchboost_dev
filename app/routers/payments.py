# app/routers/payments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud

router = APIRouter(prefix="/v1", tags=["payments"])

PLAN_AMOUNT = 700
PLAN_ATTEMPTS = 20


@router.post("/buy")
async def buy(body: dict, db: Session = Depends(get_db)):
    tg_user_id = body.get("telegram_id")
    if not tg_user_id:
        raise HTTPException(status_code=400, detail="telegram_id required")
    user = crud.get_or_create_user(db, tg_user_id)
    crud.create_payment(
        db,
        tg_user_id=tg_user_id,
        amount=PLAN_AMOUNT,
        credits=PLAN_ATTEMPTS,
        status="success",
    )
    crud.add_attempts(db, user, PLAN_ATTEMPTS)
    return {"telegram_id": tg_user_id, "new_attempts": user.attempts}
