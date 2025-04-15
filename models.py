from sqlalchemy import ForeignKey, String, ARRAY, BigInteger
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3', echo=True)

async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)


class Books(Base):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    path: Mapped[str] = mapped_column(String)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String))


class UserInterests(Base):
    __tablename__ = 'userInterests'

    id: Mapped[int] = mapped_column(primary_key=True)
    # user_id: Mapped[int] = mapped_column()
    interests: Mapped[list[str]] = mapped_column(ARRAY(String))


class Recomends(Base):
    __tablename__ = 'recomends'

    id: Mapped[int] = mapped_column(primary_key=True)
    # user_id: Mapped[int] = mapped_column()
    interests: Mapped[str] = mapped_column(String)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)