from fastapi import FastAPI
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from app.auth.routes import router as auth_router
from app.db.database import init_db
from app.api.subscriptions import router as subs_router
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Football Fan Zone AI Update")

@app.on_event("startup")
async def startup_event():
    await init_db()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(subs_router, tags=["subscriptions"])

@app.get("/")
async def root():
    return {"message": "Welcome to FFZ AI Update!"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        description="Football Fan Zone AI Update",
        routes=app.routes,
    )

    # sécurisation correcte du schéma
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # Ajoute l’exigence de sécurité sur les routes
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

from app.news.scheduler import router as news_router, start_scheduler

app.include_router(news_router)
start_scheduler()
