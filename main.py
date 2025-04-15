from contextlib import asynccontextmanager

from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import init_db
import rq


@asynccontextmanager
async def lifespan(app_: FastAPI):
    await init_db()
    print('Bot is ready ;)')
    yield

app = FastAPI(title='ai-books-app', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'], # Откуда могут приходить запросы
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('api/books')
async def books():
    return await rq.get_books()


@app.get('api/profile/{tg_id}')
async def profile(tg_id: int):
    user = await rq.add_user(tg_id)
    return {'user': user}

