import os
import uuid
import time
import mimetypes
import httpx
from datetime import datetime, timezone

import boto3
from botocore.client import Config
from loguru import logger

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://storage.yandexcloud.net")
S3_REGION = os.getenv("S3_REGION", "ru-central1")
S3_BUCKET = os.getenv("S3_BUCKET", "pitchboost-audio")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_PRESIGN_EXPIRES = int(os.getenv("S3_PRESIGN_EXPIRES", "600"))

_session = boto3.session.Session()
_s3 = _session.client(
    service_name="s3",
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(s3={"addressing_style": "path"})
)

def _object_key(user_id: str, ext: str = ".ogg") -> str:
    now = datetime.now(tz=timezone.utc)
    return f"{os.getenv('ENV','dev')}/users/{user_id}/{now:%Y/%m/%d}/{int(time.time())}_{uuid.uuid4().hex}{ext}"

class StorageService:
    """Gestión de audios en Yandex Object Storage."""
    def __init__(self, bucket: str = S3_BUCKET):
        self.bucket = bucket

    async def download_to_bytes(self, url: str) -> tuple[bytes, str]:
        # Descarga desde Telegram (o cualquier URL)
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(url)
            r.raise_for_status()
            content = r.content
            ctype = r.headers.get("Content-Type") or "audio/ogg"
            return content, ctype

    async def upload_audio_from_url(self, *, url: str, user_id: str) -> dict:
        blob, ctype = await self.download_to_bytes(url)
        ext = mimetypes.guess_extension(ctype) or ".ogg"
        key = _object_key(user_id=user_id, ext=ext)

        _s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=blob,
            ContentType=ctype,
            Metadata={"user_id": user_id}
        )
        logger.info(f"Uploaded audio to s3://{self.bucket}/{key} size={len(blob)} ctype={ctype}")
        return {"bucket": self.bucket, "key": key, "content_type": ctype, "size": len(blob)}

    def presign_get(self, key: str, expires: int = S3_PRESIGN_EXPIRES) -> str:
        return _s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires
        )

    def presign_put(self, key: str, expires: int = S3_PRESIGN_EXPIRES) -> dict:
        url = _s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires
        )
        return {"url": url, "key": key}

storage = StorageService()
