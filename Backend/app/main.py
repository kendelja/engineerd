from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.jobs import router as jobs_router
from app.scheduler import start_scheduler, stop_scheduler
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    yield

    stop_scheduler()


app = FastAPI(
    title="Engineerd API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include the jobs router
app.include_router(jobs_router)
