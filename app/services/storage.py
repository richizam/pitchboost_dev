import os
import time
import uuid
from datetime import datetime, timezone
from typing import Tuple, Dict

import boto3
import httpx

from app.core.logging import logger

# =========================
# Config desde variables
# =========================
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://storage.yandexcloud.net")
S3_REGION = os.getenv("S3_REGION", "ru-central1")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_PRESIGN_EXPIRES = int(os.getenv("S3_PRESIGN_EXPIRES", "600"))  # segundos

# Entorno lógico (dev/prod/etc)
ENV_NAME = os.getenv("ENV", "dev")

# Estilo de clave de audio: "flat" -> {env}/{uuid}.{ext}
#                          "dated" -> {env}/users/{user_id}/YYYY/MM/DD/{ts}_{uuid}.{ext}
AUDIO_KEY_STYLE = os.getenv("AUDIO_KEY_STYLE", "flat").lower()  # flat | dated


_DEFAULT_ACL = "bucket-owner-full-control"

# Cliente S3 (compatible con Yandex)
_s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)


def _guess_ext(content_type: str, default: str = ".bin") -> str:
    """Devuelve extensión a partir del Content-Type."""
    import mimetypes

    if not content_type:
        return default
    ext = mimetypes.guess_extension(content_type)
    return ext or default


def _object_key(user_id: str, content_type: str) -> str:
    """Genera la clave (Key) del objeto en el bucket según el estilo configurado."""
    ext = _guess_ext(content_type, ".bin")

    if AUDIO_KEY_STYLE == "flat":
        # ✅ Lo que pidió Nikita: {env}/{uuid}.{ext}
        return f"{ENV_NAME}/{uuid.uuid4().hex}{ext}"
    else:
        # Esquema anterior (con fecha/usuario)
        now = datetime.now(tz=timezone.utc)
        ts = int(time.time())
        return f"{ENV_NAME}/users/{user_id}/{now:%Y/%m/%d}/{ts}_{uuid.uuid4().hex}{ext}"


class StorageService:
    def __init__(self) -> None:
        self.bucket = S3_BUCKET

    async def download_to_bytes(self, url: str) -> Tuple[bytes, str]:
        """Descarga un recurso HTTP a bytes y devuelve (blob, content_type)."""
        url = str(url)  # por si llega AnyHttpUrl
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(url)
            r.raise_for_status()
            blob = r.content
            ctype = r.headers.get("Content-Type", "application/octet-stream")
            return blob, ctype

    async def upload_audio_from_url(self, *, url: str, user_id: str) -> Dict[str, str]:
        """
        Descarga un audio (por ejemplo desde Telegram) y lo sube a Object Storage.
        Devuelve dict con info: {bucket, key, size, content_type}.
        """
        blob, ctype = await self.download_to_bytes(url)

        key = _object_key(user_id=user_id, content_type=ctype)

        # Subimos con metadata útil para búsquedas/depuración
        from functools import partial
        import asyncio

        put_call = partial(
            _s3.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=blob,
            ContentType=ctype,
            Metadata={
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "telegram",
            },
            ACL=_DEFAULT_ACL,
        )

        # Ejecutar llamada de bloqueo en thread pool
        await asyncio.to_thread(put_call)

        logger.info(f"Uploaded audio to s3://{self.bucket}/{key} size={len(blob)} ctype={ctype}")
        return {
            "bucket": self.bucket,
            "key": key,
            "size": str(len(blob)),
            "content_type": ctype,
        }

    def presign_get(self, key: str) -> str:
        """Genera un URL prefirmado para GET del objeto."""
        url = _s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=S3_PRESIGN_EXPIRES,
        )
        return url


# Instancia global
storage = StorageService()
