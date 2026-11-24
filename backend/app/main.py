import uvicorn
from fastapi import FastAPI

from app.routes.screenings import router as screenings_router


def create_app() -> FastAPI:
    app = FastAPI(title="Cinema API")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(screenings_router)
    return app


app = create_app()


def main() -> None:
    uvicorn.run("app.main:app", reload=True)


if __name__ == "__main__":
    main()
