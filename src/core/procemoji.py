import datetime
import asyncio
import aiohttp

import base64
import io
from PIL import Image

import sqlalchemy as sqla

from core import util
from core import logging
from core import permission as perm
from core import exc
from core import wsmsg
from core import procrisk
from core.db import database, model

from front import websocket
from misskey import miapi


# add or update
async def update_emoji(data_emoji, ws_send=True, emoji_log=None):
    changes = {}
    async with database.db_sessionmaker() as db_session:
        data_owner = data_emoji['user']

        emoji_mid = data_emoji['id']

        new = False

        try:
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == emoji_mid).limit(1)
            emoji = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            emoji = model.Emoji()
            emoji.id = util.randid()
            emoji.misskey_id = emoji_mid
            new = True

        emoji_id = emoji.id

        emoji_name = data_emoji['name']
        emoji_category = data_emoji['category']
        emoji_tags = ' '.join(data_emoji['aliases'])
        emoji_is_self_made = data_emoji['isSelfMadeResource']
        emoji_license = data_emoji['license']
        emoji_url = data_emoji['url']

        if not new:
            if emoji_name != emoji.name:
                before = emoji.name
                changes['emoji_name'] = (before, emoji_name)
            if emoji_category != emoji.category:
                before = emoji.category
                changes['emoji_category'] = (before, emoji_category)
            if emoji_tags != emoji.tags:
                before = emoji.tags
                changes['emoji_tags'] = (before, emoji_tags)
            if emoji_is_self_made != emoji.is_self_made:
                before = emoji.is_self_made
                changes['emoji_is_self_made'] = (before, emoji_is_self_made)
            if emoji_license != emoji.license:
                before = emoji.license
                changes['emoji_license'] = (before, emoji_license)
            if emoji_url != emoji.url:
                before = emoji.url
                changes['emoji_url'] = (before, emoji_url)

        emoji.name = emoji_name
        emoji.category = emoji_category
        emoji.tags = emoji_tags

        emoji.is_self_made = 1 if emoji_is_self_made else 0
        emoji.license = emoji_license

        emoji.url = emoji_url
        
        if emoji_log is None:
            elog = await miapi.get_emoji_log(emoji_mid)
        else:
            elog = emoji_log
        if new:
            t = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc).isoformat()
            if len(elog) > 0:
                if elog[0]['type'] == 'Add':
                    t = elog[0]['createDate']
                    tu = t
                for i in reversed(range(len(elog))):
                    if elog[i]['type'] == 'Update':
                        tu = elog[i]['createDate']
                        break
            else:
                tu = t
            emoji.created_at = t
            emoji.updated_at = tu
        else:
            t = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc).isoformat()
            if len(elog) > 0:
                for i in reversed(range(len(elog))):
                    if elog[i]['type'] == 'Update':
                        t = elog[i]['createDate']
                        break
            if datetime.datetime.fromisoformat(emoji.updated_at) >= datetime.datetime.fromisoformat(t):
                if ws_send:
                    return emoji_id
                else:
                    return emoji_id, None
            emoji.updated_at = t
        
        created_at = emoji.created_at
        updated_at = emoji.updated_at

        uid = None
        new_user = False

        if data_owner is not None:

            umid = data_owner['id']
            umnm = data_owner['username']

            try:
                query = sqla.select(model.User).where(model.User.misskey_id == umid).limit(1)
                user = (await db_session.execute(query)).one()[0]
                uid = user.id
            except sqla.exc.NoResultFound:
                new_user = True
                user = model.User()
                uid = util.randid()
                user.id = uid
                user.misskey_id = umid
                user.username = umnm

                msg = wsmsg.UserUpdate(uid, umid, umnm).build()
                await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)

                db_session.add(user)

        emoji.user_id = uid

        update_checked = False

        if new:
            rid = await procrisk.create_risk(emoji_mid)
            emoji.risk_id = rid
        else:
            rid = emoji.risk_id
            try:
                query = sqla.select(model.Risk).where(model.Risk.id == rid).limit(1)
                risk = (await db_session.execute(query)).one()[0]
                if risk.is_checked == 1:
                    update_checked = True
            except sqla.exc.NoResultFound:
                rid = procrisk.create_risk(emoji_mid)
                emoji.risk_id = rid

        db_session.add(emoji)

        await db_session.commit()

    if update_checked:
        await procrisk.update_risk(rid, {'checked': 2})

    if new:
        await logging.write(None,
        {
            'op': 'create_emoji',
            'body': {
                'id': emoji_id,
                'misskey_id': emoji_mid,
                'name': emoji_name,
                'category': emoji_category,
                'tags': emoji_tags,
                'is_self_made': emoji_is_self_made,
                'license': emoji_license,
                'user_id': uid,
                'url': emoji_url,
                'risk_id': rid,
            }
        })
    else:
        await logging.write(None,
        {
            'op': 'update_emoji',
            'body': {
                'id': emoji_id,
                'changes': changes,
            }
        })
    if new_user:
        await logging.write(None,
        {
            'op': 'create_user',
            'body': {
                'id': uid,
                'misskey_id': umid,
                'username': umnm,
            }
        })

    if ws_send:
        msg = wsmsg.EmojiUpdate(emoji_id, data_emoji, uid, rid, created_at, updated_at).build()
        await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)
        return emoji_id
    else:
        return emoji_id, wsmsg._EmojiData(emoji_id, data_emoji, uid, rid, created_at, updated_at)

async def delete_emoji(data_emoji, ws_send=True):
    async with database.db_sessionmaker() as db_session:
        emoji_mid = data_emoji['id']

        try:
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == emoji_mid).limit(1)
            emoji = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            return

        emoji_id = emoji.id
        emoji_name = emoji.name
        emoji_category = emoji.category
        emoji_tags = emoji.tags
        emoji_is_self_made = emoji.is_self_made
        emoji_license = emoji.license
        emoji_url = emoji.url

        uid = emoji.user_id
        rid = emoji.risk_id

        await db_session.delete(emoji)

        await db_session.commit()

    async def capture_image():
        image_b64 = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(emoji_url) as res:
                    if res.status == 200:
                        data = await res.content.read()
            with Image.open(io.BytesIO(data)) as image:
                fi =  image.format
                if fi in ['JPEG', 'PNG', 'WebP']:
                    image.thumbnail((128, 128))
                    with io.BytesIO() as out:
                        image.save(out, format='PNG')
                        image_b64 = base64.b64encode(out.getvalue()).decode()
                elif fi == 'GIF':
                    info = image.info
                    loop = 0
                    duration = 100
                    if 'loop' in info:
                        loop = info['loop']
                    if 'duration' in info:
                        duration = info['duration']
                    frames = []
                    for index in range(image.n_frames):
                        image.seek(index)
                        frames.append(image.copy().thumbnail((128, 128)))
                    with io.BytesIO() as out:
                        frames[0].save(out, format='GIF', save_all=True, append_images=frames[1:], loop=loop, duration=duration)
                        image_b64 = base64.b64encode(out.getvalue()).decode()
                else:
                    return
        except Exception:
            import traceback
            traceback.print_exc()
        return image_b64

    image_b64 = await asyncio.create_task(capture_image())

    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

    async with database.db_sessionmaker() as db_session:
        deleted = model.DeletedEmoji()

        deleted.id = emoji_id
        deleted.misskey_id = emoji_mid
        deleted.name = emoji_name
        deleted.category = emoji_category
        deleted.tags = emoji_tags
        deleted.is_self_made = emoji_is_self_made
        deleted.license = emoji_license
        deleted.risk_id = rid
        deleted.user_id = uid
        deleted.url = emoji_url
        deleted.image_backup = image_b64
        deleted.info = ''
        deleted.deleted_at = now

        db_session.add(deleted)

        await db_session.commit()

    if image_b64 is None:
        image_backup_trunc = None
    else:
        if len(image_b64) <= 64:
            image_backup_trunc = image_b64
        else:
            image_backup_trunc = image_b64[:64] + '... (Truncated)'

    await logging.write(None,
    {
        'op': 'delete_emoji',
        'body': {
            'id': emoji_id,
            'misskey_id': emoji_mid,
            'name': emoji_name,
            'category': emoji_category,
            'tags': emoji_tags,
            'is_self_made': emoji_is_self_made,
            'license': emoji_license,
            'user_id': uid,
            'url': emoji_url,
            'image_backup': image_backup_trunc,
            'risk_id': rid,
        }
    })

    if emoji_tags == '':
        ltags = []
    else:
        ltags = emoji_tags.split(' ')

    if ws_send:
        msg = wsmsg.EmojiDelete(emoji_id).build()
        await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)
        msg = wsmsg.DeletedEmojiUpdate(emoji_id, emoji_mid, emoji_name, emoji_category, ltags, emoji_url, image_b64, emoji_is_self_made, emoji_license, uid, rid, '', now).build()
        await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)
        return
    else:
        return emoji_id

async def set_deleted_reason(eid, info, ws=None):
    async with database.db_sessionmaker() as db_session:
        try:
            query = sqla.select(model.DeletedEmoji).where(model.DeletedEmoji.id == eid).limit(1)
            deleted = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            raise exc.NoSuchEmojiException()

        emoji_id = deleted.id
        emoji_mid = deleted.misskey_id
        emoji_name = deleted.name
        emoji_category = deleted.category
        emoji_tags = deleted.tags
        emoji_is_self_made = deleted.is_self_made
        emoji_license = deleted.license
        rid = deleted.risk_id
        uid = deleted.user_id
        emoji_url = deleted.url
        emoji_image_backup = deleted.image_backup
        deleted_at = deleted.deleted_at

        if emoji_tags == '':
            ltags = []
        else:
            ltags = emoji_tags.split(' ')

        if deleted.info != info:
            before = deleted.info
            deleted.info = info

            await db_session.commit()

            await logging.write(ws,
            {
                'op': 'update_deleted_reason',
                'body': {
                    'id': eid,
                    'change': [before, info]
                }
            })

            msg = wsmsg.DeletedEmojiUpdate(emoji_id, emoji_mid, emoji_name, emoji_category, ltags, emoji_url, emoji_image_backup, emoji_is_self_made, emoji_license, uid, rid, info, deleted_at).build()
            await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)


async def plune_emoji(exsits_mids):
    async with database.db_sessionmaker() as db_session:

        pluning_mids = []
        eids = []

        query = sqla.select(model.Emoji)
        results = await db_session.stream(query)
        async for part in results.partitions(10):
            for result in part:
                mid = result[0].misskey_id
                if mid not in exsits_mids:
                    pluning_mids.append(mid)
        
        for mid in pluning_mids:
            eid = await delete_emoji({'id': mid}, False)
            eids.append(eid)
    msg = wsmsg.EmojisDelete(eids).build()
    await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)


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
