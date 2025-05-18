from fastapi import FastAPI
from app.api import health, term, obj

app = FastAPI()

app.include_router(health.router)
app.include_router(term.router)
app.include_router(obj.router)

