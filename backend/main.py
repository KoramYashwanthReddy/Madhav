from fastapi import FastAPI
from backend.core.health import router as health_router

app = FastAPI(
    title="Madhav Personal AI",
    description="Madhav Personal AI Core Engine",
    version="0.1.0",
)

app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
