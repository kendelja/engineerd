from fastapi import FastAPI
from app.api.jobs import router as jobs_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Engineerd API",
    version="1.0.0"
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