# kafka_client
# app/services/kafka_client.py
import json
import uuid
from typing import Any, Dict

from confluent_kafka import Producer

from app.core.config import settings
from app.core.logging import logger


def _delivery_report(err, msg):
    if err is not None:
        logger.error(f"Kafka delivery failed: {err}")
    else:
        logger.info(
            f"Kafka delivered to {msg.topic()} [{msg.partition()}] offset={msg.offset()}"
        )


class KafkaGatewayProducer:
    def __init__(self):
        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": settings.KAFKA_CLIENT_ID,
        }
        self._producer = Producer(conf)
        self._topic_in = settings.KAFKA_TOPIC_IN

    def enqueue_for_processing(self, payload: Dict[str, Any]) -> str:
        """
        Envía el mensaje JSON a processing y devuelve trace_id (si no viene, lo genera).
        """
        trace_id = payload.get("trace_id") or uuid.uuid4().hex
        payload["trace_id"] = trace_id

        value = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._producer.produce(self._topic_in, value=value, callback=_delivery_report)
        # Empuja el evento de IO
        self._producer.poll(0)
        logger.info(f"Produced to {self._topic_in}: trace_id={trace_id}")
        return trace_id

    def flush(self):
        try:
            self._producer.flush(5.0)
        except Exception:
            pass


kafka_producer = KafkaGatewayProducer()
