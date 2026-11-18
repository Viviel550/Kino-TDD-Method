from fastapi import FastAPI

def main():
    uvicorn.run("app.main:app", reload=True)

def create_app() -> FastAPI:
    app = FastAPI(title="Cinema API")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_app()
