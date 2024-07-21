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


# ==================================================
#                   Tool <-> Server                 
# ==================================================

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
        asyncio.create_task(send_alldata(ws))
        await ws.wait_closed()
    except Exception:
        traceback.print_exc()
        ws.close()
    finally:
        print('websocket connection closed')
        unregister(ws)


async def send_alldata(ws):
    async with db_sessionmaker() as db_session:
        query = sqla.select(model.Emoji, model.User).outerjoin(model.User, model.Emoji.user_id == model.User.id)
        results = await db_session.stream(query)
        async for part in results.partitions(10):
            for result in part:
                emoji, user = result

                eid = emoji.id
                misskey_id = emoji.misskey_id
                name = emoji.name
                category = emoji.category
                tags = emoji.tags
                url = emoji.url
                created_at = emoji.created_at
                updated_at = emoji.updated_at

                user_id = user.misskey_id
                user_name = user.username

                msg = wsmsg.EmojiUpdated(eid, None, created_at, updated_at, misskey_id=misskey_id, name=name, category=category, tags=tags, url=url, owner_mid=user_id, owner_name=user_name).build()
                await ws.send(msg)


# ==================================================
#                   Data processing                 
# ==================================================


def randid():
    return str(uuid.uuid4())


# add or update
async def update_emoji(data_emoji):
    async with db_sessionmaker() as db_session:
        data_owner = data_emoji['user']

        emoji_mid = data_emoji['id']

        new = False

        try:
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == emoji_mid).limit(1)
            emoji = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            emoji = model.Emoji()
            emoji.id = randid()
            emoji.misskey_id = emoji_mid
            new = True

        emoji_id = emoji.id

        emoji.name = data_emoji['name']
        emoji.category = data_emoji['category']
        emoji.tags = ' '.join(data_emoji['aliases'])
        emoji.url = data_emoji['url']
        
        elog = await get_emoji_log(emoji_mid)
        if new:
            t = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc).isoformat()
            if len(elog) > 0:
                if elog[0]['type'] == 'Add':
                    t = elog[0]['createDate']
            emoji.created_at = t
            emoji.updated_at = t
        else:
            t = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc).isoformat()
            if len(elog) > 0:
                for i in reversed(range(len(elog))):
                    if elog[i]['type'] == 'Update':
                        t = elog[i]['createDate']
                        break
            if datetime.datetime.fromisoformat(emoji.updated_at) >= datetime.datetime.fromisoformat(t):
                return
            emoji.updated_at = t
        
        created_at = emoji.created_at
        updated_at = emoji.updated_at

        umid = data_owner['id']
        umnm = data_owner['username']
        
        try:
            query = sqla.select(model.User).where(model.User.misskey_id == umid)
            user = (await db_session.execute(query)).one()[0]
            uid = user.id
        except sqla.exc.NoResultFound:
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

    msg = wsmsg.EmojiUpdated(emoji_id, data_emoji, created_at, updated_at).build()
    await broadcast(msg)

async def delete_emoji(data_emoji):
    async with db_sessionmaker() as db_session:
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

async def misskey_emojis_updated(data):
    data_emojis = data['emojis']
    for data_emoji in data_emojis:
        await update_emoji(data_emoji)

async def misskey_emojis_deleted(data):
    data_emojis = data['emojis']
    for data_emoji in data_emojis:
        await delete_emoji(data_emoji)


# ==================================================
#                 Server <-> Misskey                
# ==================================================


async def observe_emoji_change():
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
                                await misskey_emojis_updated(j['body'])
                            case 'emojiDeleted':
                                await misskey_emojis_deleted(j['body'])
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
        async with session.post(uri, json=params) as res:
            data = await res.json()
    return data

async def update_all_emojis():
    uri = f'{HTTP_SCHEME}://{MISSKEY_HOST}/api/admin/emoji/list'

    until = None
    async with aiohttp.ClientSession() as session:
        while True:
            params = {'limit': 100, 'i': MISSKEY_TOKEN}
            if until is not None:
                params['untilId'] = until
            async with session.post(uri, json=params) as res:
                data_emojis = await res.json()
                if len(data_emojis) == 0: break

                for data_emoji in data_emojis:
                    await update_emoji(data_emoji)
                
                until = data_emojis[-1]['id']

async def periodical_update_all_emojis(t):
    while True:
        await asyncio.sleep(t)
        await update_all_emojis()


# ==================================================
#                        Main                       
# ==================================================

async def main():
    await update_all_emojis()

    task_observe_emoji = asyncio.create_task(observe_emoji_change())
    task_update_all_emojis = asyncio.create_task(periodical_update_all_emojis(3600))

    try:
        async with websockets.serve(connect, HOST, PORT):
            await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        print('Exit server')

    task_observe_emoji.cancel()
    task_update_all_emojis.cancel()



if __name__ == '__main__':

    db_engine = create_async_engine(f'sqlite+aiosqlite:///{DBPATH}', echo=True)

    async def db_init():
        async with db_engine.begin() as conn:
            await conn.run_sync(model.Base.metadata.create_all)
    asyncio.run(db_init())

    db_sessionmaker = sessionmaker(bind=db_engine, class_=AsyncSession, autoflush=True)

    asyncio.run(main())


