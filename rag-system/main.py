import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging import logger

app = FastAPI(
    title="Multimodal Google Drive RAG System API",
    description="Production-quality RAG system answering questions accurately over Google Drive text, tables, and diagrams.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def startup_event():
    logger.info("Multimodal Google Drive RAG API service starting up.")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Multimodal Google Drive RAG API service shutting down.")


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
