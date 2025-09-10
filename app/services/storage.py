# storage.py
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Tuple, Dict

import boto3
import httpx
from fastapi import HTTPException

from app.core.logging import logger
from app.core.config import settings

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://storage.yandexcloud.net")
S3_REGION = os.getenv("S3_REGION", "ru-central1")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_PRESIGN_EXPIRES = int(os.getenv("S3_PRESIGN_EXPIRES", "600"))
ENV_NAME = os.getenv("ENV", "dev")
AUDIO_KEY_STYLE = os.getenv("AUDIO_KEY_STYLE", "flat").lower()  # flat | dated

_DEFAULT_ACL = "bucket-owner-full-control"

_s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
)


ALLOWED_TYPES = {"audio/ogg": ".ogg", "audio/mpeg": ".mp3", "audio/wav": ".wav"}


def _guess_ext(content_type: str, url: str, default: str = ".bin") -> str:
    if content_type in ALLOWED_TYPES:
        return ALLOWED_TYPES[content_type]
    lower = url.lower()
    if lower.endswith(".oga") or lower.endswith(".ogg"):
        return ".ogg"
    return default


def _object_key(user_id: str, content_type: str, url: str) -> str:
    ext = _guess_ext(content_type, url, ".bin")
    if AUDIO_KEY_STYLE == "flat":
        return f"{ENV_NAME}/{uuid.uuid4().hex}{ext}"
    else:
        now = datetime.now(tz=timezone.utc)
        ts = int(time.time())
        return f"{ENV_NAME}/users/{user_id}/{now:%Y/%m/%d}/{ts}_{uuid.uuid4().hex}{ext}"


class StorageService:
    def __init__(self) -> None:
        self.bucket = S3_BUCKET

    async def download_to_bytes(self, url: str) -> Tuple[bytes, str]:
        url = str(url)
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            head = await client.head(url)
            size = head.headers.get("Content-Length")
            if size and int(size) > settings.AUDIO_MAX_CONTENT_LENGTH:
                raise HTTPException(status_code=400, detail="Audio too large")
            r = await client.get(url)
            r.raise_for_status()
            blob = r.content
            ctype = r.headers.get("Content-Type", "application/octet-stream")
            return blob, ctype

    async def upload_audio_from_url(self, *, url: str, user_id: str) -> Dict[str, str]:
        blob, ctype = await self.download_to_bytes(url)
        key = _object_key(user_id=user_id, content_type=ctype, url=url)

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
        await asyncio.to_thread(put_call)

        logger.info(
            f"Uploaded audio to s3://{self.bucket}/{key} size={len(blob)} ctype={ctype}"
        )
        return {
            "bucket": self.bucket,
            "key": key,
            "size": str(len(blob)),
            "content_type": ctype,
        }

    def presign_get(self, key: str) -> str:
        url = _s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=S3_PRESIGN_EXPIRES,
        )
        return url


storage = StorageService()
