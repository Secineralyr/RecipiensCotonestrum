import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import close_all_sessions
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

    db_sessionmaker = async_sessionmaker(bind=db_engine, autoflush=True)

def close():
    global db_engine, db_sessionmaker
    if db_engine is not None:
        asyncio.run(close_all_sessions())
        asyncio.run(db_engine.dispose())
        db_engine = None
        db_sessionmaker = None


