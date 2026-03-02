import time

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.routes import router
from app.core.config import settings
from app.db.database import Base, engine

app = FastAPI(title=settings.app_name)
app.include_router(router, prefix=settings.api_prefix)


@app.on_event("startup")
def init_database() -> None:
    max_attempts = 15
    retry_delay_seconds = 2

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError:
            if attempt == max_attempts:
                raise
            time.sleep(retry_delay_seconds)


@app.get("/health")
def health():
    return {"status": "ok"}
