from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import router as api_router
from bot_runtime import start_bot_task, stop_bot_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_bot_task()
    try:
        yield
    finally:
        await stop_bot_task()


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
