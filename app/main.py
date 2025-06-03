from fastapi import FastAPI
from app.api import health, objects, requisites, references, terms
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi

app = FastAPI()
security = HTTPBearer()

# Переопределяем openapi-схему
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Integram API",
        version="0.1.0",
        description="API for Integram",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(health.router)
app.include_router(terms.router)
app.include_router(objects.router)
app.include_router(requisites.router)
app.include_router(references.router)

