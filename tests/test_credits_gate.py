from app.core.config import settings
import app.services.storage as storage
from app.services.kafka_client import kafka_producer


async def fake_upload_audio_from_url(url: str, user_id: str):
    return {"bucket": "b", "key": "k", "size": "1", "content_type": "audio/ogg"}


def setup_mocks(monkeypatch):
    monkeypatch.setattr(
        storage.storage, "upload_audio_from_url", fake_upload_audio_from_url
    )
    monkeypatch.setattr(kafka_producer, "enqueue_for_processing", lambda payload: None)
    monkeypatch.setattr(kafka_producer, "flush", lambda: None)


def analyze(client):
    return client.post(
        "/v1/analyze",
        json={
            "user_id": "u1",
            "scenario": "investor",
            "duration_minutes": 1,
            "audio_url": "http://example.com/a.ogg",
            "media_duration_sec": 10,
        },
    )


def test_credits_gate(client, monkeypatch):
    setup_mocks(monkeypatch)
    for _ in range(settings.FREE_CREDITS):
        resp = analyze(client)
        assert resp.status_code == 202
    resp = analyze(client)
    assert resp.status_code == 402
    pay = client.post("/v1/pay", json={"tg_user_id": "u1", "amount": 2})
    assert pay.status_code == 200
    resp = analyze(client)
    assert resp.status_code == 202
