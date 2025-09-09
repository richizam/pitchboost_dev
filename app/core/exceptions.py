#exceptions.py
from fastapi import HTTPException, status

class BadAudioException(HTTPException):
    def __init__(self, detail="Invalid audio"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
