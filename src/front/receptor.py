from functools import wraps
import traceback

import sqlalchemy as sqla

from core import wsmsg
from core import permission as perm
from core import exc
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


@receptor('fetch_all', perm.Permission.EMOJI_MODERATOR)
async def send_alldata(ws, body):
    async with database.db_sessionmaker() as db_session:
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

                msg = wsmsg.EmojiUpdate(eid, None, created_at, updated_at, misskey_id=misskey_id, name=name, category=category, tags=tags, url=url, owner_mid=user_id, owner_name=user_name).build()
                await ws.send(msg)

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
