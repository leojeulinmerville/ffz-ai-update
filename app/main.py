from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from dotenv import load_dotenv

from app.db.database import init_db
from app.auth.routes import router as auth_router
from app.api.subscriptions import router as subs_router
from app.api.news import router as news_router

# NEW: scheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduler.jobs import schedule_jobs

# charge .env
load_dotenv()

# instance FastAPI
app = FastAPI(title="Football Fan Zone AI Update")

# instance globale du scheduler
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup_event():
    # 1. init DB (crée les tables si besoin)
    await init_db()

    # 2. enregistrer les jobs cron (lundi 09h Europe/Paris)
    schedule_jobs(scheduler)

    # 3. démarrer le scheduler
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    # arrêter le scheduler proprement
    scheduler.shutdown(wait=False)

# inclure les routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(subs_router, tags=["subscriptions"])
app.include_router(news_router, tags=["news"])

@app.get("/")
async def root():
    return {"message": "Welcome to FFZ AI Update!"}

# -------- OPENAPI SECURITY (Bearer dans Swagger) --------

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        description="Football Fan Zone AI Update",
        routes=app.routes,
    )

    # Déclare le schéma JWT Bearer
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # Ajoute automatiquement `Authorization: Bearer <token>` requis
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            # on ne force PAS l'auth sur /auth/*
            tags = operation.get("tags", [])
            if "auth" in tags:
                continue
            operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
