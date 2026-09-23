"""Application entry point for MADHAV platform foundation."""

from madhav.core.application import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("madhav.main:app", host="0.0.0.0", port=8000, reload=True)
