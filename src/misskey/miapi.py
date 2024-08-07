import aiohttp

from env import envs

from json.decoder import JSONDecodeError
from aiohttp.client_exceptions import ContentTypeError

import sqlalchemy as sqla

from core import util
from core import wsmsg
from core import permission as perm
from core import procemoji
from core import exc
from core.db import database, model

from front import websocket

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


async def authenticate(token):
    uri = f'{HTTP_SCHEME}://{MISSKEY_HOST}/api/i'
    async with aiohttp.ClientSession() as session:
        params = {'i': token}
        async with session.post(uri, json=params) as res:
            try:
                data = await res.json()
                if 'message' in data:
                    raise exc.MiAPIErrorException(data)
            except (ContentTypeError, JSONDecodeError):
                raise exc.MiUnknownErrorException()

    async with database.db_sessionmaker() as db_session:
        umid = data['id']
        umnm = data['username']

        try:
            query = sqla.select(model.User).where(model.User.misskey_id == umid).limit(1)
            user = (await db_session.execute(query)).one()[0]
            uid = user.id
        except sqla.exc.NoResultFound:
            user = model.User()
            uid = util.randid()
            user.id = uid
            user.misskey_id = umid
            user.username = umnm

            db_session.add(user)
            await db_session.commit()

            msg = wsmsg.UserUpdate(uid, umid, umnm).build()
            await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)

    if data['isAdmin']:
        level = perm.Permission.ADMINISTRATOR
    elif data['isModerator']:
        level = perm.Permission.MODERATOR
    elif data['isEmojiModerator']:
        level = perm.Permission.EMOJI_MODERATOR
    else:
        level = perm.Permission.USER
    return uid, level

async def get_emoji_log(emoji_mid):
    uri = f'{HTTP_SCHEME}://{MISSKEY_HOST}/api/admin/emoji/get-emoji-log'
    async with aiohttp.ClientSession() as session:
        params = {'id': emoji_mid, 'i': MISSKEY_TOKEN}
        async with session.post(uri, json=params) as res:
            try:
                data = await res.json()
                if 'message' in data:
                    raise exc.MiAPIErrorException(data)
            except (ContentTypeError, JSONDecodeError):
                raise exc.MiUnknownErrorException()
    return data

async def update_all_emojis():
    uri = f'{HTTP_SCHEME}://{MISSKEY_HOST}/api/admin/emoji/list'

    until = None
    exists = []
    async with aiohttp.ClientSession() as session:
        while True:
            params = {'limit': 100, 'i': MISSKEY_TOKEN}
            if until is not None:
                params['untilId'] = until
            async with session.post(uri, json=params) as res:
                try:
                    data_emojis = await res.json()
                    if 'message' in data_emojis:
                        raise exc.MiAPIErrorException(data_emojis)
                except (ContentTypeError, JSONDecodeError):
                    raise exc.MiUnknownErrorException()
                
                if len(data_emojis) == 0: break

                for data_emoji in data_emojis:
                    await procemoji.update_emoji(data_emoji)
                    exists.append(data_emoji['id'])
                
                until = data_emojis[-1]['id']
    
    await procemoji.plune_emoji(exists)

