from functools import wraps
import traceback

import sqlalchemy as sqla

from core import wsmsg
from core import permission as perm
from core import exc
from core import error
from core import procrisk
from core.db import database, model

from front import websocket
from misskey import miapi


receptors = {}

def receptor(op: str, req_level: perm.Permission = perm.Permission.USER):
    def _receptor(func):
        g = func.__globals__
        g['_op'] = op

        @perm.require(req_level)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            _op = op
            await func(*args, **kwargs)
        
        receptors[op] = wrapper
        return wrapper
    return _receptor


@receptor('auth', perm.Permission.USER)
async def authenticate(ws, body):
    try:
        level = await miapi.authenticate(body['token'])
    except exc.MiAPIErrorException as ex:
        traceback.print_exc()
        msg = wsmsg.MisskeyAPIError(globals()['_op'], ex.err).build()
        await websocket.broadcast(msg)
    except exc.MiUnknownErrorException:
        traceback.print_exc()
        msg = wsmsg.MisskeyUnknownError(globals()['_op'], '').build()
        await websocket.broadcast(msg)
    else:
        websocket.connections[ws]['level'] = level

@receptor('fetch_emoji', perm.Permission.EMOJI_MODERATOR)
async def send_emoji(ws, body):
    eid = body['id']
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.Emoji).where(model.Emoji.id == eid).limit(1)
        try:
            emoji = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            error.send_no_such_emoji(ws, globals()['_op'], eid)
        else:
            misskey_id = emoji.misskey_id
            name = emoji.name
            category = emoji.category
            tags = emoji.tags
            url = emoji.url
            is_self_made = emoji.is_self_made
            license = emoji.license
            created_at = emoji.created_at
            updated_at = emoji.updated_at

            uid = emoji.user_id

            msg = wsmsg.EmojiUpdate(eid, None, uid, created_at, updated_at, misskey_id=misskey_id, name=name, category=category, tags=tags, url=url, is_self_made=is_self_made, license=license, owner_mid=user_id, owner_name=user_name).build()
            await ws.send(msg)

@receptor('fetch_all_emojis', perm.Permission.EMOJI_MODERATOR)
async def send_all_emojis(ws, body):
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.Emoji)
        results = await db_session.stream(query)
        async for part in results.partitions(10):
            for result in part:
                emoji = result[0]

                eid = emoji.id
                misskey_id = emoji.misskey_id
                name = emoji.name
                category = emoji.category
                tags = emoji.tags
                url = emoji.url
                is_self_made = emoji.is_self_made
                license = emoji.license
                created_at = emoji.created_at
                updated_at = emoji.updated_at

                uid = emoji.user_id

                msg = wsmsg.EmojiUpdate(eid, None, uid, created_at, updated_at, misskey_id=misskey_id, name=name, category=category, tags=tags, url=url, is_self_made=is_self_made, license=license, owner_mid=user_id, owner_name=user_name).build()
                await ws.send(msg)

@receptor('fetch_user', perm.Permission.EMOJI_MODERATOR)
async def send_user(ws, body):
    uid = body['id']
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.User).where(model.User.id == uid).limit(1)
        try:
            user = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            error.send_no_such_user(ws, globals()['_op'], uid)
        else:
            misskey_id = user.misskey_id
            username = user.username

            msg = wsmsg.UserUpdate(uid, misskey_id, username).build()
            await ws.send(msg)

@receptor('fetch_all_users', perm.Permission.EMOJI_MODERATOR)
async def send_all_users(ws, body):
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.User)
        results = await db_session.stream(query)
        async for part in results.partitions(10):
            for result in part:
                user = result[0]

                uid = user.id
                misskey_id = user.misskey_id
                username = user.username

                msg = wsmsg.UserUpdate(uid, misskey_id, username).build()
                await ws.send(msg)

@receptor('set_risk_prop', perm.Permission.EMOJI_MODERATOR)
async def set_risk_prop(ws, body):
    rid = body['id']
    props = body['props']
    try:
        procrisk.set_risk(rid, props)
    except exc.NoSuchRiskException:
        error.send_no_such_risk(ws, globals()['_op'], rid)
