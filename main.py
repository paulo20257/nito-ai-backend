import logging
from decimal import Decimal, ROUND_HALF_UP
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zangui-credito")

app = FastAPI(title="ZANGUI CRÉDITO API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

class SimulationRequest(BaseModel):
    amount: Decimal = Field(ge=4000, le=400000)
    months: int = Field(ge=3, le=24)
    monthly_rate: Decimal = Field(default=Decimal("0.03"), ge=0, le=Decimal("0.08"))

@app.get("/")
async def home():
    return {"app": "ZANGUI CRÉDITO", "status": "online", "mode": "demonstration"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/config")
async def config():
    return {
        "brand": "ZANGUI CRÉDITO",
        "currency": "AOA",
        "minimum_amount": 4000,
        "maximum_amount": 400000,
        "minimum_months": 3,
        "maximum_months": 24,
        "applications_enabled": False,
        "notice": "Simulações ilustrativas. Não são propostas nem aprovação de crédito."
    }

@app.post("/api/simular")
async def simulate(data: SimulationRequest):
    principal = data.amount
    rate = data.monthly_rate
    months = data.months
    if rate == 0:
        payment = principal / months
    else:
        factor = (Decimal(1) + rate) ** months
        payment = principal * rate * factor / (factor - Decimal(1))
    total = (payment * months).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    installment = payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "ok": True,
        "currency": "AOA",
        "principal": str(principal),
        "months": months,
        "illustrative_monthly_rate": str(rate),
        "estimated_monthly_payment": str(installment),
        "estimated_total": str(total),
        "estimated_interest": str((total - principal).quantize(Decimal("0.01"))),
        "notice": "Estimativa demonstrativa; encargos e condições reais não estão definidos."
    }

@app.post("/api/pedidos")
async def applications_disabled():
    raise HTTPException(
        status_code=503,
        detail="A receção de pedidos reais está desativada. O serviço só poderá ser ativado após implementação de segurança, proteção de dados e validação legal."
    )
