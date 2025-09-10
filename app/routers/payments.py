# app/routers/payments.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud

router = APIRouter(prefix="/v1", tags=["payments"])

PLAN_AMOUNT = 700
PLAN_CREDITS = 20


@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(tg_user_id: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang=\"ru\">
<head>
<meta charset=\"UTF-8\"/>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>
<title>Оплата</title>
<style>
 body {{
   font-family: Arial, sans-serif;
   background-color: #f5f5f5;
   margin: 0;
   display: flex;
   justify-content: center;
   align-items: center;
   height: 100vh;
 }}
 .card {{
   background: #fff;
   padding: 2rem;
   border-radius: 8px;
   box-shadow: 0 2px 8px rgba(0,0,0,0.1);
   text-align: center;
   max-width: 300px;
   width: 100%;
 }}
 button {{
   background: #4CAF50;
   color: white;
   border: none;
   padding: 0.75rem 1.5rem;
   border-radius: 4px;
   font-size: 1rem;
   cursor: pointer;
 }}
 button:hover {{
   background: #45a049;
 }}
</style>
</head>
<body>
<div class=\"card\">
  <h2>20 попыток</h2>
  <p>700 ₽</p>
  <button onclick=\"pay()\">Оплатить</button>
</div>
<script>
async function pay() {{
  const res = await fetch('/v1/checkout', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{tg_user_id: '{tg_user_id}'}})
  }});
  if (res.ok) {{
    document.body.innerHTML = '<h2 style=\"text-align:center;\">Оплачено</h2>';
  }}
}}
</script>
</body>
</html>
"""
    )


@router.post("/checkout")
async def process_checkout(body: dict, db: Session = Depends(get_db)):
    tg_user_id = body.get("tg_user_id")
    if not tg_user_id:
        raise HTTPException(status_code=400, detail="tg_user_id required")
    user = crud.get_or_create_user(db, tg_user_id)
    crud.create_payment(
        db,
        tg_user_id=tg_user_id,
        amount=PLAN_AMOUNT,
        credits=PLAN_CREDITS,
        status="success",
    )
    crud.add_paid_credits(db, user, PLAN_CREDITS)
    return {"status": "ok"}
