from sqlalchemy import select, update, delete, func
from models import async_session, Books, User, UserInterests
from pydantic import BaseModel, ConfigDict
from typing import List


class BooksSchema(BaseModel):
    id: int
    title: str
    author: str
    description: str
    path: str
    tags: list[str]

    model_config = ConfigDict(from_attributes=True)


async def add_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            return user
        
        new_user = User(tg_id = tg_id)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
    

async def get_books():
    async with async_session() as session:
        books = await session.scalars(
            select(Books)
        )

        serialized_books = [
            BooksSchema.model_validate(b).model_dump() for b in books
        ]

        return serialized_books