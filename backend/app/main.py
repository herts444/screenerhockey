import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models.database import init_db
from .api.routes import router
from .services.sync_service import sync_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    print("Starting up...")
    init_db()

    # Load data for all leagues on startup
    print("Loading initial data...")
    try:
        await sync_service.sync_all(force=False)
    except Exception as e:
        print(f"Error during initial sync: {e}")

    # Start scheduler for automatic updates at 12:00
    sync_service.start_scheduler()

    yield

    # Shutdown
    print("Shutting down...")
    await sync_service.close()


app = FastAPI(
    title="NHL/AHL Screener API",
    description="API for NHL and AHL match statistics and analysis",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "NHL/AHL Screener API",
        "docs": "/docs",
        "version": "2.0.0",
        "features": [
            "In-memory caching",
            "Automatic sync at 12:00 daily",
            "NHL and AHL support"
        ]
    }
