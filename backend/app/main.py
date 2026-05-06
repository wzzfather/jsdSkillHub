from contextlib import asynccontextmanager

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import AsyncSessionLocal
from app.routers import auth, reviews, scans, skills, workflow
from app.services.seed import run_startup_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as session:
        await run_startup_seed(session)
    yield


app = FastAPI(title="Enterprise Agent App Store API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(skills.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
app.include_router(workflow.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
