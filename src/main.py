import os
import traceback

import uuid
import datetime
import json

import asyncio
import aiohttp
import websockets

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


# add or update
async def update_emoji(data_emoji):
    data_owner = data_emoji['user']

    emoji_mid = data_emoji['id']

    try:
        query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == emoji_mid).limit(1)
        emoji = (await db_session.execute(query)).one()[0]
    except sqla.exc.NoResultFound:
        emoji = model.Emoji()
        emoji.id = randid()
        emoji.misskey_id = emoji_mid

    emoji.name = data_emoji['name']
    emoji.category = data_emoji['category']
    emoji.tags = ' '.join(data_emoji['aliases'])
    emoji.url = data_emoji['url']
    
    elog = get_emoji_log(emoji_mid)
    if emoji_mid == None:
        t = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc).isoformat()
        if len(elog) > 0:
            if elog[0]['type'] == 'Add':
                t = elog[0]['createDate']
        emoji.created_at = t
        emoji.updated_at = t
    else:
        if len(elog) > 0:
            for i in reversed(len(elog)):
                if elog[i]['type'] == 'Update':
                    emoji.updated_at = elog[i]['createDate']
                    break
    
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

    msg = wsmsg.EmojiUpdated(emoji.id, data_emoji, emoji.created_at, emoji.updated_at).build()
    await broadcast(msg)

async def delete_emoji(data_emoji):
    emoji_mid = data_emoji['id']

    try:
        query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == emoji_mid).limit(1)
        emoji = (await db_session.execute(query)).one()[0]
    except sqla.exc.NoResultFound:
        return

    emoji_id = emoji.id
    
    msg = wsmsg.EmojiDeleted(emoji_id).build()

    await broadcast(msg)








async def misskey_emoji_added(data):
    data_emoji = data['emoji']
    await update_emoji(data_emoji)

async def misskey_emoji_updated(data):
    data_emojis = data['emojis']
    for data_emoji in data_emojis:
        await update_emoji(data_emoji)

async def misskey_emoji_deleted(data):
    data_emojis = data['emojis']
    for data_emoji in data_emojis:
        await delete_emoji(data_emoji)


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

async def get_emoji_log(emoji_mid):
    uri = f'{HTTP_SCHEME}://{MISSKEY_HOST}/api/admin/emoji/get-emoji-log'
    async with aiohttp.ClientSession() as session:
        params = {'id': emoji_mid, 'i': MISSKEY_TOKEN}
        async with session.post(uri, data=json.dumps(params)) as res:
            data = await res.json()
    return data


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


