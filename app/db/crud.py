from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import models


def get_or_create_user(db: Session, tg_user_id: str) -> models.User:
    stmt = select(models.User).where(models.User.tg_user_id == tg_user_id)
    user = db.execute(stmt).scalar_one_or_none()
    if user:
        return user
    user = models.User(tg_user_id=tg_user_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_tg_id(db: Session, tg_user_id: str) -> models.User | None:
    stmt = select(models.User).where(models.User.tg_user_id == tg_user_id)
    return db.execute(stmt).scalar_one_or_none()


def increment_free_used(db: Session, user: models.User) -> None:
    user.credits_free_used += 1
    db.add(user)
    db.commit()


def decrement_paid_credit(db: Session, user: models.User) -> None:
    if user.credits_paid > 0:
        user.credits_paid -= 1
        db.add(user)
        db.commit()


def add_paid_credits(db: Session, user: models.User, amount: int) -> None:
    user.credits_paid += amount
    db.add(user)
    db.commit()


def create_pitch(
    db: Session,
    *,
    user_id: int,
    audio_key: str,
    scenario: str,
    duration_minutes: int,
    status: str,
) -> models.Pitch:
    pitch = models.Pitch(
        user_id=user_id,
        audio_key=audio_key,
        scenario=scenario,
        duration_minutes=duration_minutes,
        status=status,
    )
    db.add(pitch)
    db.commit()
    db.refresh(pitch)
    return pitch


def list_pitches(db: Session, user_id: int, limit: int = 10) -> list[models.Pitch]:
    stmt = (
        select(models.Pitch)
        .where(models.Pitch.user_id == user_id)
        .order_by(models.Pitch.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars())
