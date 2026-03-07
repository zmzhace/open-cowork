from dotenv import load_dotenv
load_dotenv()  # Load .env before any other imports that use env vars

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.api.routes import router
from src.database import Base, engine
import logging

logger = logging.getLogger("uvicorn.error")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Open-Cowork API", version="0.1.0")

# Log 422 validation errors clearly
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"422 Validation Error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc.errors())},
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Open-Cowork API"}

