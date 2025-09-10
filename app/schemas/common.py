# app/schemas/common.py
from pydantic import BaseModel


class Scores(BaseModel):
    clarity: int
    structure: int
    persuasion: int
    total: int
