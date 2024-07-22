import datetime

import sqlalchemy as sqla

from core import util
from core import wsmsg
from core.db import database, model

from front import websocket
from misskey import miapi

# add or update
async def update_emoji(data_emoji):
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

        emoji.name = data_emoji['name']
        emoji.category = data_emoji['category']
        emoji.tags = ' '.join(data_emoji['aliases'])
        emoji.url = data_emoji['url']
        
        elog = await miapi.get_emoji_log(emoji_mid)
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
            uid = util.randid()
            user.id = uid
            user.misskey_id = umid
            user.username = umnm

            db_session.add(user)
            await db_session.commit()

        emoji.user_id = uid

        db_session.add(emoji)
        await db_session.commit()

    msg = wsmsg.EmojiUpdated(emoji_id, data_emoji, created_at, updated_at).build()
    await websocket.broadcast(msg)

async def delete_emoji(data_emoji):
    async with database.db_sessionmaker() as db_session:
        emoji_mid = data_emoji['id']

        try:
            query = sqla.select(model.Emoji).where(model.Emoji.misskey_id == emoji_mid).limit(1)
            emoji = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            return

        emoji_id = emoji.id
    
    msg = wsmsg.EmojiDeleted(emoji_id).build()
    await websocket.broadcast(msg)


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