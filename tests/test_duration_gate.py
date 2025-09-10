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


def test_duration_gate(client, monkeypatch):
    setup_mocks(monkeypatch)
    resp = client.post(
        "/v1/analyze",
        json={
            "user_id": "u1",
            "scenario": "recommendation",
            "duration_minutes": 1,
            "audio_url": "http://example.com/a.ogg",
            "media_duration_sec": settings.AUDIO_MAX_SECONDS + 1,
        },
    )
    assert resp.status_code == 400

    resp = client.post(
        "/v1/analyze",
        json={
            "user_id": "u1",
            "scenario": "recommendation",
            "duration_minutes": 1,
            "audio_url": "http://example.com/a.ogg",
            "media_duration_sec": settings.AUDIO_MAX_SECONDS - 1,
        },
    )
    assert resp.status_code == 202
