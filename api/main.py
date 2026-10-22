from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import projects, assets, timeline, subtitles, audio, render, overlays

app = FastAPI(title="Renderline API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router)
app.include_router(assets.router)
app.include_router(timeline.router)
app.include_router(subtitles.router)
app.include_router(audio.router)
app.include_router(overlays.router)
app.include_router(render.router)


@app.get("/")
def root():
    return {"message": "Video Script Engine API"}


@app.get("/health")
def health():
    return {"status": "ok"}
