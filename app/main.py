# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.routers import health, analyze, users, payments

app = FastAPI(title="PitchBoost API Gateway")
app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)
app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(users.router)
app.include_router(payments.router)
