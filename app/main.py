# app/main.py
from fastapi import FastAPI
from app.routers import health, analyze, users, payments

app = FastAPI(title="PitchBoost API Gateway")
app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(users.router)
app.include_router(payments.router)
