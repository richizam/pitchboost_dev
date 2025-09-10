import app.services.storage as storage
from app.services.kafka_client import kafka_producer


async def fake_upload_audio_from_url(url: str, user_id: str):
    return {"bucket": "b", "key": "k123", "size": "1", "content_type": "audio/ogg"}


def test_kafka_payload_shape_with_duration(client, monkeypatch):
    monkeypatch.setattr(
        storage.storage, "upload_audio_from_url", fake_upload_audio_from_url
    )
    captured = {}

    def fake_enqueue(payload):
        captured["payload"] = payload

    monkeypatch.setattr(kafka_producer, "enqueue_for_processing", fake_enqueue)
    monkeypatch.setattr(kafka_producer, "flush", lambda: None)

    resp = client.post(
        "/v1/analyze",
        json={
            "user_id": "u1",
            "scenario": "adaptation",
            "duration_minutes": 1,
            "audio_url": "http://example.com/a.ogg",
            "media_duration_sec": 10,
        },
    )
    assert resp.status_code == 202
    payload = captured["payload"]
    assert set(payload.keys()) == {
        "user_id",
        "audio_id",
        "request_message",
        "scenario",
        "duration_minutes",
    }


def test_kafka_payload_shape_without_duration(client, monkeypatch):
    monkeypatch.setattr(
        storage.storage, "upload_audio_from_url", fake_upload_audio_from_url
    )
    captured = {}

    def fake_enqueue(payload):
        captured["payload"] = payload

    monkeypatch.setattr(kafka_producer, "enqueue_for_processing", fake_enqueue)
    monkeypatch.setattr(kafka_producer, "flush", lambda: None)

    resp = client.post(
        "/v1/analyze",
        json={
            "user_id": "u1",
            "scenario": "recommendation",
            "audio_url": "http://example.com/a.ogg",
            "media_duration_sec": 10,
        },
    )
    assert resp.status_code == 202
    payload = captured["payload"]
    assert set(payload.keys()) == {
        "user_id",
        "audio_id",
        "request_message",
        "scenario",
    }
