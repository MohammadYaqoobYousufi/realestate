# Real Estate AI API Entry Point
from fastapi import FastAPI
from app.api import valuation, governance

app = FastAPI(title="Calgary Real Estate Intelligence Platform")

app.include_router(valuation.router, prefix="/valuation")
app.include_router(governance.router, prefix="/governance")