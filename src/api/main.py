from fastapi import FastAPI

from src.api.routes import router
from src.config.version import PROJECT_NAME, VERSION

app = FastAPI(title=PROJECT_NAME, version=VERSION)

app.include_router(router)


@app.get("/")
def root():
    return {"project": PROJECT_NAME, "version": VERSION, "docs": "/docs"}
