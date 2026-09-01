import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .core.database import engine, Base
from .core.config import settings
from .api import routes_v1, routes_input, routes_videos, routes_analysis, routes_queries, routes_search, routes_jobs, routes_process

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url="/api/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(routes_v1.router, prefix="/api", tags=["Android Mobile API v1"])
app.include_router(routes_input.router, prefix="/api", tags=["Inputs"])
app.include_router(routes_videos.router, prefix="/api", tags=["Videos"])
app.include_router(routes_analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(routes_queries.router, prefix="/api", tags=["Queries"])
app.include_router(routes_search.router, prefix="/api", tags=["Search"])
app.include_router(routes_jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(routes_process.router, prefix="/api", tags=["Process"])

# Serve Frontend SPA
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
static_dir = os.path.join(frontend_dir, "static")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Douyin Content Finder Backend API is running! Visit /api/docs"}
