import os
import traceback

import uuid
import datetime

import json

import asyncio
import websockets

import aiosqlite

import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from env import envs
import model
import wsmsg


HOST = envs['HOST']
PORT = int(envs['PORT'])

DBPATH = envs['DBPATH']

MISSKEY_HOST = envs['MISSKEY_HOST']
MISSKEY_TOKEN = envs['MISSKEY_TOKEN']

# for local-env test
NO_SSL = False
if 'NO_SSL' in envs:
    if envs['NO_SSL'] == '1':
        NO_SSL = True

if NO_SSL:
    HTTP_SCHEME = 'http'
    WS_SCHEME = 'ws'
else:
    HTTP_SCHEME = 'https'
    WS_SCHEME = 'wss'


connections = {}

async def broadcast(msg, exclude=None):
    conns = set(connections) - {exclude,}
    websockets.broadcast(conns, msg)

def register(ws):
    connections[ws] = {}

def unregister(ws):
    del connections[ws]

async def connect(ws, path):
    register(ws)
    print('websocket connection opened')
    try:
        await ws.wait_closed()
    except Exception:
        traceback.print_exc()
        ws.close()
    finally:
        print('websocket connection closed')
        unregister(ws)




def randid():
    return str(uuid.uuid4())

async def misskey_emoji_added(data):
    data_emoji = data['emoji']
    data_owner = data_emoji['user']

    emoji_id = randid()

    emoji = model.Emoji()
    emoji.id = emoji_id
    emoji.misskey_id = data_emoji['id']
    emoji.name = data_emoji['name']
    emoji.category = data_emoji['category']
    emoji.tags = ' '.join(data_emoji['aliases'])
    emoji.url = data_emoji['url']

    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    emoji.created_at = now
    emoji.updated_at = now

    umid = data_owner['id']
    umnm = data_owner['username']
    
    query = sqla.select(sqla.func.count()).select_from(model.User).where(model.User.misskey_id == umid)
    if await db_session.scalar(query) == 0:
        user = model.User()
        uid = randid()
        user.id = uid
        user.misskey_id = umid
        user.username = umnm

        db_session.add(user)
        await db_session.commit()

    emoji.user_id = uid

    db_session.add(emoji)
    await db_session.commit()

    msg = wsmsg.EmojiUpdated(emoji_id, data, now, now).build()
    await broadcast(msg)

async def misskey_emoji_updated(data):

    data_emojis = data['emojis']

    for data_emoji in data_emojis:
        data_owner = data_emoji['user']

        emoji_mid = data_emoji['id']

        try:
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == emoji_mid).limit(1)
            emoji = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            return

        emoji_id = emoji.id
        
        emoji.name = data_emoji['name']
        emoji.category = data_emoji['category']
        emoji.tags = ' '.join(data_emoji['aliases'])
        emoji.url = data_emoji['url']

        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        created_at = emoji.created_at
        emoji.updated_at = now

        uid = data_owner['id']
        unm = data_owner['username']
        
        query = sqla.select(sqla.func.count()).select_from(model.User).where(model.User.misskey_id == uid)
        if await db_session.scalar(query) == 0:
            user = model.User()
            user.id = randid()
            user.misskey_id = uid
            user.username = unm

            db_session.add(user)
            await db_session.commit()

        emoji.user_id = uid

        db_session.add(emoji)
        await db_session.commit()

        msg = wsmsg.EmojiUpdated(emoji_id, data, created_at, now).build()

        await broadcast(msg)

async def misskey_emoji_deleted(data):
    data_emojis = data['emojis']

    for data_emoji in data_emojis:
        emoji_mid = data_emoji['id']

        try:
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == emoji_mid).limit(1)
            emoji = (await db_session.execute(query)).one()
        except sqla.exc.NoResultFound:
            return

        emoji_id = emoji.id
        
        msg = wsmsg.EmojiDeleted(emoji_id).build()

        await broadcast(msg)


async def misskey_observe_emoji_change():
    while True:
        uri = f'{WS_SCHEME}://{MISSKEY_HOST}/streaming?i={MISSKEY_TOKEN}'
        try:
            async with websockets.connect(uri) as ws:
                while True:
                    data = await ws.recv()
                    try:
                        print(data)
                        j = json.loads(data)
                        match j['type']:
                            case 'emojiAdded':
                                await misskey_emoji_added(j['body'])
                            case 'emojiUpdated':
                                await misskey_emoji_updated(j['body'])
                            case 'emojiDeleted':
                                await misskey_emoji_deleted(j['body'])
                    except Exception:
                        traceback.print_exc()
        except websockets.ConnectionClosed:
            pass
        except Exception:
            traceback.print_exc()


async def main():
    task_observe_emoji = asyncio.create_task(misskey_observe_emoji_change())
    
    async with websockets.serve(connect, HOST, PORT):
        await asyncio.Future()  # run forever



if __name__ == '__main__':

    db_engine = create_async_engine(f'sqlite+aiosqlite:///{DBPATH}', echo=True)

    async def db_init():
        async with db_engine.begin() as conn:
            await conn.run_sync(model.Base.metadata.create_all)
    asyncio.run(db_init())

    db_session = sessionmaker(bind=db_engine, class_=AsyncSession, autoflush=True)()


    asyncio.run(main())


