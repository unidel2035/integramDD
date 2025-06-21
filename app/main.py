from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi

from app.api import health, objects, requisites, references, terms
from app.middleware.auth_middleware import AuthMiddleware


app = FastAPI()
app.add_middleware(AuthMiddleware)
security = HTTPBearer()

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
            "description": "Enter your JWT token like this (without Bearer): your_token"
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

