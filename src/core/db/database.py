import asyncio

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from env import envs

from core.db import model


DBPATH = envs['DBPATH']

db_engine = None
db_sessionmaker = None

def init():
    global db_engine, db_sessionmaker
    db_engine = create_async_engine(f'sqlite+aiosqlite:///{DBPATH}', echo=True)

    async def db_init():
        async with db_engine.begin() as conn:
            await conn.run_sync(model.Base.metadata.create_all)
    asyncio.run(db_init())

    db_sessionmaker = sessionmaker(bind=db_engine, class_=AsyncSession, autoflush=True)

