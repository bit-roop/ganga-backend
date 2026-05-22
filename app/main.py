from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.incidents import router as incidents_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.services.incident_service import seed_incidents_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_incidents_if_empty()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(incidents_router, prefix="/api")

media_directory = Path(settings.media_root)
media_directory.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_directory), name="media")
