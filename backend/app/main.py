import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, dev, health, tickets
from app.config import settings
from app.db.session import engine
from app.errors import register_error_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s v%s starting", settings.app_name, settings.app_version)
    yield
    await engine.dispose()
    logger.info("engine disposed")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(tickets.router, prefix=settings.api_v1_prefix)
if settings.dev_auth:
    # Router dev hanya didaftarkan kalau DEV_AUTH=true -> endpoint benar-benar tidak ada.
    app.include_router(dev.router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": f"{settings.api_v1_prefix}/health",
    }
