# tests/test_checkout.py
from sqlalchemy import select

from app.db import models
from app.db.database import get_db


def test_buy_adds_attempts_and_payment(client):
    tg_id = "42"
    r = client.post("/v1/buy", json={"telegram_id": tg_id})
    assert r.status_code == 200
    data = r.json()
    assert data["telegram_id"] == tg_id
    assert data["new_attempts"] == 20

    r = client.get(f"/v1/balance/{tg_id}")
    data = r.json()
    assert data["attempts"] == 20

    override = client.app.dependency_overrides[get_db]
    db = next(override())
    try:
        payments = (
            db.execute(select(models.Payment).where(models.Payment.tg_user_id == tg_id))
            .scalars()
            .all()
        )
    finally:
        db.close()
    assert len(payments) == 1
    assert payments[0].amount == 700
    assert payments[0].credits == 20
