# tests/test_checkout.py
from sqlalchemy import select

from app.db import models
from app.db.database import get_db


def test_checkout_adds_credits_and_payment(client):
    tg_id = "42"
    r = client.post("/v1/checkout", json={"tg_user_id": tg_id})
    assert r.status_code == 200

    r = client.get(f"/v1/credits/{tg_id}")
    data = r.json()
    assert data["paid"] == 20

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
