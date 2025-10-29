from fastapi import FastAPI
from app.auth.routes import router as auth_router
from app.db.database import init_db

app = FastAPI(title="Football Fan Zone AI Update")

@app.on_event("startup")
async def startup_event():
    await init_db()

app.include_router(auth_router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Welcome to FFZ AI Update!"}
