class StorageService:
    async def resolve_audio_url(self, audio_url: str) -> str:
        # En CP1 solo valido url; en CP2 integro S3/MinIO o presigned URLs
        return audio_url

storage = StorageService()
