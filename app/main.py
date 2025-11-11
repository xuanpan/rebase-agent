"""
FastAPI Application for Rebase Agent.

Main application module that initializes the FastAPI app, configures
middleware, and sets up API routes for chat-first transformation analysis.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager
import os
from loguru import logger

from .api.v1 import chat, transformations, analysis, projects
from .config import Settings
from .dependencies import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting Rebase Agent...")
    
    # Initialize core components
    settings = get_settings()
    
    # Add any startup logic here (database connections, etc.)
    logger.info("Rebase Agent started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Rebase Agent...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    settings = get_settings()
    
    app = FastAPI(
        title="Rebase Agent",
        description="AI Intelligence Layer for business-focused transformation analysis",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Add API routes
    app.include_router(
        chat.router,
        prefix="/api/v1",
        tags=["chat"]
    )
    
    app.include_router(
        transformations.router,
        prefix="/api/v1", 
        tags=["transformations"]
    )
    
    app.include_router(
        analysis.router,
        prefix="/api/v1",
        tags=["analysis"] 
    )
    
    app.include_router(
        projects.router,
        prefix="/api/v1",
        tags=["projects"]
    )
    
# Enhanced chat functionality is now unified in the main chat router
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Rebase Agent - AI Intelligence Layer",
            "version": "0.1.0",
            "docs": "/docs"
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    # For development - use `uvicorn app.main:app --reload` for production
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )