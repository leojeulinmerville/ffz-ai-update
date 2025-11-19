import logging
import subprocess
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Response, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.api.admin_page import router as admin_router
from app.api.meta import router as meta_router
from app.api.scrape import router as scrape_router
from app.api.facts import router as facts_router
from app.api.news import router as news_router
from app.api.subscriptions import router as subs_router
from app.auth.routes import router as auth_router
from app.models.db import init_db, engine
from app.scheduler.jobs import schedule_jobs

load_dotenv()

logger = logging.getLogger("ffz.main")
SCHEMA_ERROR_MSG: Optional[str] = None


async def _ensure_database_current() -> None:
    alembic_cfg = Config('alembic.ini')
    script = ScriptDirectory.from_config(alembic_cfg)
    head_revision = script.get_current_head()

    async with engine.begin() as conn:
        def _current_revision(sync_conn):
            context = MigrationContext.configure(sync_conn)
            return context.get_current_revision()

        current_revision = await conn.run_sync(_current_revision)

    if current_revision != head_revision:
        raise RuntimeError(
            f"Database schema out of date (current={current_revision}, head={head_revision}). "
            "Please run 'alembic upgrade head' inside the api container."
        )
app = FastAPI(title="Football Fan Zone AI Update")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

scheduler = AsyncIOScheduler()

@app.middleware("http")
async def schema_guard(request: Request, call_next):
    if SCHEMA_ERROR_MSG:
        return JSONResponse(
            {
                "detail": SCHEMA_ERROR_MSG,
                "hint": "Run 'docker compose -f docker/docker-compose.yml exec api alembic upgrade head'",
            },
            status_code=503,
        )
    return await call_next(request)


@app.on_event("startup")
async def startup_event() -> None:
    global SCHEMA_ERROR_MSG
    await init_db()
    try:
        await _ensure_database_current()
        SCHEMA_ERROR_MSG = None
    except RuntimeError as exc:
        SCHEMA_ERROR_MSG = str(exc)
        logger.error("Database not ready: %s", exc)
        # Tenter d'exécuter les migrations automatiquement
        logger.info("Attempting to run migrations automatically...")
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.info("Migrations completed successfully")
                SCHEMA_ERROR_MSG = None
                # Vérifier à nouveau
                await _ensure_database_current()
            else:
                logger.error("Migration failed: %s", result.stderr)
        except Exception as migration_exc:
            logger.warning("Auto-migration failed: %s", migration_exc)
        logger.warning("Scheduler will start anyway but may fail until database is migrated")
    
    # Toujours démarrer le scheduler, même si la DB n'est pas prête
    # Le job gérera les erreurs de DB de manière robuste
    schedule_jobs(scheduler)
    scheduler.start()
    logger.info("Scheduler started successfully")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(meta_router)
app.include_router(admin_router)
app.include_router(subs_router)
app.include_router(news_router)
app.include_router(facts_router)
app.include_router(scrape_router)


@app.get("/health")
async def health_check():
    """Endpoint de health check pour Railway et autres plateformes."""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.running if scheduler else False,
        "database_ready": SCHEMA_ERROR_MSG is None,
    }


@app.get("/")
async def root():
    return {"message": "Welcome to FFZ AI Update!"}


@app.get("/favicon.ico")
async def favicon() -> Response:
    return Response(content=b"", media_type="image/x-icon")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="0.1.0",
        description="Football Fan Zone AI Update",
        routes=app.routes,
    )

    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            tags = operation.get("tags", [])
            if "auth" in tags:
                continue
            operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
