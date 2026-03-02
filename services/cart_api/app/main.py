from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.db.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix=settings.api_prefix)


@app.get("/health")
def health():
    return {"status": "ok"}
