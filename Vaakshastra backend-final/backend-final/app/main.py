"""
VaakShastra Backend - Final working version
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting VaakShastra backend...")
    await init_db()
    Path("./uploads").mkdir(parents=True, exist_ok=True)
    Path("./static").mkdir(parents=True, exist_ok=True)
    yield
    print("Shutting down...")


app = FastAPI(
    title="VaakShastra API",
    description="AI Legal Assistant for Indian Courts",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow ALL origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from app.routers import auth, documents, analysis

app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"app": "VaakShastra", "status": "running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Serve frontend from /site (put your index.html in the static/ folder)
app.mount("/site", StaticFiles(directory="static", html=True), name="static")
