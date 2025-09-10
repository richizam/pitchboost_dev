import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import get_db
from app.db import models
import app.services.kafka_client as kafka_client


class _DummyProducer:
    def enqueue_for_processing(self, payload):
        pass

    def flush(self):
        pass


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    models.Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(kafka_client, "kafka_producer", _DummyProducer())
    with TestClient(app) as c:
        yield c
    monkeypatch.undo()
    app.dependency_overrides.clear()
