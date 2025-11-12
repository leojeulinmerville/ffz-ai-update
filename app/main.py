import logging
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
    except RuntimeError as exc:
        SCHEMA_ERROR_MSG = str(exc)
        logger.error("Database not ready: %s", exc)
        return
    schedule_jobs(scheduler)
    scheduler.start()


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
