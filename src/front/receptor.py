from functools import wraps
import traceback

import sqlalchemy as sqla

from core import wsmsg
from core import permission as perm
from core import exc
from core import error
from core import procemoji, procrisk
from core import procreason
from core.db import database, model

from front import websocket
from misskey import miapi


receptors = {}

def receptor(op: str, req_level: perm.Permission = perm.Permission.USER):
    def _receptor(func):

        @perm.require(op, req_level)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            g = func.__globals__

            old = g.get('_op', object())
            g['_op'] = op

            try:
                ret = await func(*args, **kwargs)
            finally:
                if old is object():
                    del g['_op']
                else:
                    g['_op'] = old
            
            return ret
        
        receptors[op] = wrapper
        return wrapper
    return _receptor


@receptor('auth', perm.Permission.NO_CREDENTIAL)
async def authenticate(ws, body, reqid):
    try:
        uid, level, username = await miapi.authenticate(body['token'], ws)
    except exc.MiAPIErrorException as ex:
        traceback.print_exc()
        return wsmsg.MisskeyAPIError(globals()['_op'], ex.err, reqid).build()
    except exc.MiUnknownErrorException:
        traceback.print_exc()
        return wsmsg.MisskeyUnknownError(globals()['_op'], '', reqid).build()
    else:
        perm.set_level(ws, perm.Permission(level))
        websocket.connections[ws]['uid'] = uid
        return wsmsg.OK(globals()['_op'], reqid, f"You logged in as '{perm.get_name(level)}'. (Username: {username})").build()

@receptor('fetch_emoji', perm.Permission.EMOJI_MODERATOR)
async def send_emoji(ws, body, reqid):
    eid = body['id']
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.Emoji).where(model.Emoji.id == eid).limit(1)
        try:
            emoji = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            return error.no_such_emoji(globals()['_op'], eid, reqid)
        else:
            misskey_id = emoji.misskey_id
            name = emoji.name
            category = emoji.category
            tags = emoji.tags
            if tags == '':
                ltags = []
            else:
                ltags = tags.split(' ')
            url = emoji.url
            is_self_made = emoji.is_self_made
            license = emoji.license
            created_at = emoji.created_at
            updated_at = emoji.updated_at

            uid = emoji.user_id
            rid = emoji.risk_id

            msg = wsmsg.EmojiUpdate(eid, None, uid, rid, created_at, updated_at, misskey_id=misskey_id, name=name, category=category, tags=ltags, url=url, is_self_made=is_self_made, license=license).build()
            await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_all_emojis', perm.Permission.EMOJI_MODERATOR)
async def send_all_emojis(ws, body, reqid):
    emojis_data = []
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
                if tags == '':
                    ltags = []
                else:
                    ltags = tags.split(' ')
                url = emoji.url
                is_self_made = emoji.is_self_made
                license = emoji.license
                created_at = emoji.created_at
                updated_at = emoji.updated_at

                uid = emoji.user_id
                rid = emoji.risk_id

                emoji_data = wsmsg._EmojiData(eid, None, uid, rid, created_at, updated_at, misskey_id=misskey_id, name=name, category=category, tags=ltags, url=url, is_self_made=is_self_made, license=license)
                emojis_data.append(emoji_data)
    msg = wsmsg.EmojisUpdate(emojis_data).build()
    await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_deleted_emoji', perm.Permission.EMOJI_MODERATOR)
async def send_deleted_emoji(ws, body, reqid):
    eid = body['id']
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.DeletedEmoji).where(model.DeletedEmoji.id == eid).limit(1)
        try:
            deleted = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            return error.no_such_emoji(globals()['_op'], eid, reqid)
        else:
            misskey_id = deleted.misskey_id
            name = deleted.name
            category = deleted.category
            tags = deleted.tags
            if tags == '':
                ltags = []
            else:
                ltags = tags.split(' ')
            url = deleted.url
            image_backup = deleted.image_backup
            is_self_made = deleted.is_self_made
            license = deleted.license
            info = deleted.info
            deleted_at = deleted.deleted_at

            uid = deleted.user_id
            rid = deleted.risk_id

            msg = wsmsg.DeletedEmojiUpdate(eid, misskey_id, name, category, ltags, url, image_backup, is_self_made, license, uid, rid, info, deleted_at).build()
            await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_all_deleted_emojis', perm.Permission.EMOJI_MODERATOR)
async def send_all_deleted_emojis(ws, body, reqid):
    emojis_data = []
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.DeletedEmoji)
        results = await db_session.stream(query)
        async for part in results.partitions(10):
            for result in part:
                deleted = result[0]

                eid = deleted.id
                misskey_id = deleted.misskey_id
                name = deleted.name
                category = deleted.category
                tags = deleted.tags
                if tags == '':
                    ltags = []
                else:
                    ltags = tags.split(' ')
                url = deleted.url
                image_backup = deleted.image_backup
                is_self_made = deleted.is_self_made
                license = deleted.license
                info = deleted.info
                deleted_at = deleted.deleted_at

                uid = deleted.user_id
                rid = deleted.risk_id

                emoji_data = wsmsg._DeletedEmojiData(eid, misskey_id, name, category, ltags, url, image_backup, is_self_made, license, uid, rid, info, deleted_at)
                emojis_data.append(emoji_data)
    msg = wsmsg.DeletedEmojisUpdate(emojis_data).build()
    await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_user', perm.Permission.EMOJI_MODERATOR)
async def send_user(ws, body, reqid):
    uid = body['id']
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.User).where(model.User.id == uid).limit(1)
        try:
            user = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            return error.no_such_user(globals()['_op'], uid, reqid)
        else:
            misskey_id = user.misskey_id
            username = user.username

            msg = wsmsg.UserUpdate(uid, misskey_id, username).build()
            await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_all_users', perm.Permission.EMOJI_MODERATOR)
async def send_all_users(ws, body, reqid):
    users_data = []
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.User)
        results = await db_session.stream(query)
        async for part in results.partitions(10):
            for result in part:
                user = result[0]

                uid = user.id
                misskey_id = user.misskey_id
                username = user.username

                user_data = wsmsg._UserData(uid, misskey_id, username)
                users_data.append(user_data)
    msg = wsmsg.UsersUpdate(users_data).build()
    await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_risk', perm.Permission.EMOJI_MODERATOR)
async def send_risk(ws, body, reqid):
    rid = body['id']
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.Risk).where(model.Risk.id == rid).limit(1)
        try:
            risk = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            return error.no_such_risk(globals()['_op'], rid, reqid)
        else:
            checked = risk.is_checked
            level = risk.level
            reason_genre = risk.reason_genre
            remark = risk.remark
            created_at = risk.created_at
            updated_at = risk.updated_at

            msg = wsmsg.RiskUpdate(rid, checked, level, reason_genre, remark, created_at, updated_at).build()
            await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_all_risks', perm.Permission.EMOJI_MODERATOR)
async def send_all_risks(ws, body, reqid):
    risks_data = []
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.Risk)
        results = await db_session.stream(query)
        async for part in results.partitions(10):
            for result in part:
                risk = result[0]

                rid = risk.id
                checked = risk.is_checked
                level = risk.level
                reason_genre = risk.reason_genre
                remark = risk.remark
                created_at = risk.created_at
                updated_at = risk.updated_at

                risk_data = wsmsg._RiskData(rid, checked, level, reason_genre, remark, created_at, updated_at)
                risks_data.append(risk_data)
    msg = wsmsg.RisksUpdate(risks_data).build()
    await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_reason', perm.Permission.EMOJI_MODERATOR)
async def send_reason(ws, body, reqid):
    rsid = body['id']
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.Reason).where(model.Reason.id == rsid).limit(1)
        try:
            reason = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            return error.no_such_reason(globals()['_op'], rsid, reqid)
        else:
            text = reason.reason
            created_at = reason.created_at
            updated_at = reason.updated_at

            msg = wsmsg.ReasonUpdate(rsid, text, created_at, updated_at).build()
            await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('fetch_all_reasons', perm.Permission.EMOJI_MODERATOR)
async def send_all_reasons(ws, body, reqid):
    reasons_data = []
    async with database.db_sessionmaker() as db_session:
        query = sqla.select(model.Reason)
        results = await db_session.stream(query)
        async for part in results.partitions(10):
            for result in part:
                reason = result[0]

                rsid = reason.id
                text = reason.reason
                created_at = reason.created_at
                updated_at = reason.updated_at

                reason_data = wsmsg._ReasonData(rsid, text, created_at, updated_at)
                reasons_data.append(reason_data)
    msg = wsmsg.ReasonsUpdate(reasons_data).build()
    await ws.send(msg)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('set_risk_prop', perm.Permission.EMOJI_MODERATOR)
async def set_risk_prop(ws, body, reqid):
    rid = body['id']
    props = body['props']
    try:
        await procrisk.update_risk(rid, props, ws=ws)
    except exc.NoSuchRiskException:
        return error.no_such_risk(globals()['_op'], rid, reqid)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('set_deleted_reason', perm.Permission.EMOJI_MODERATOR)
async def set_deleted_reason(ws, body, reqid):
    eid = body['id']
    info = body['info']
    try:
        await procemoji.set_deleted_reason(eid, info, ws=ws)
    except exc.NoSuchEmojiException:
        return error.no_such_emoji(globals()['_op'], eid, reqid)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('create_reason', perm.Permission.EMOJI_MODERATOR)
async def create_reason(ws, body, reqid):
    text = body['text']
    await procreason.create_reason(text, ws=ws)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('delete_reason', perm.Permission.EMOJI_MODERATOR)
async def delete_reason(ws, body, reqid):
    rsid = body['id']
    try:
        await procreason.delete_reason(rsid, ws=ws)
    except exc.NoSuchReasonException:
        return error.no_such_reason(globals()['_op'], rsid, reqid)
    return wsmsg.OK(globals()['_op'], reqid).build()

@receptor('set_reason_text', perm.Permission.EMOJI_MODERATOR)
async def set_reason_text(ws, body, reqid):
    rsid = body['id']
    text = body['text']
    try:
        await procreason.update_reason(rsid, text, ws=ws)
    except exc.NoSuchReasonException:
        return error.no_such_reason(globals()['_op'], rsid, reqid)
    return wsmsg.OK(globals()['_op'], reqid).build()

