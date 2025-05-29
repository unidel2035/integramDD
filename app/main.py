from fastapi import FastAPI
from app.api import health, objects, requisites, references, terms

app = FastAPI()

app.include_router(health.router)
app.include_router(terms.router)
app.include_router(objects.router)
app.include_router(requisites.router)
app.include_router(references.router)

