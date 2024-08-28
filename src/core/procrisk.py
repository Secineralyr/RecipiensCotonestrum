import datetime

import sqlalchemy as sqla

from core import util
from core import logging
from core import permission as perm
from core import wsmsg
from core import exc
from core.db import database, model

from front import websocket


# is_checked
#  0 -> no checked (require check)
#  1 -> checked
#  2 -> updated emoji after check (require re-check)

async def create_risk(emoji_misskey_id, ws=None):
    new = False
    async with database.db_sessionmaker() as db_session:
        try:
            query = sqla.select(model.Risk).where(model.Risk.emoji_misskey_id == emoji_misskey_id).limit(1)
            risk = (await db_session.execute(query)).one()[0]
            rid = risk.id
        except sqla.exc.NoResultFound:
            new = True

            now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            rid = util.randid()

            risk = model.Risk()
            risk.emoji_misskey_id = emoji_misskey_id
            risk.id = rid
            risk.is_checked = 0
            risk.level = None
            risk.reason_genre = None
            risk.remark = ''
            risk.created_at = now
            risk.updated_at = now

            db_session.add(risk)

            await db_session.commit()

    if new:
        await logging.write(ws,
        {
            'op': 'create_risk',
            'body': {
                'id': rid,
                'is_checked': 0,
                'level': 0,
                'reason_genre': None,
                'remark': '',
            }
        })

        msg = wsmsg.RiskUpdate(rid, 0, 0, None, '', now, now).build()
        await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)

    return rid


async def update_risk(rid, props, ws=None):
    async with database.db_sessionmaker() as db_session:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        try:
            query = sqla.select(model.Risk).where(model.Risk.id == rid).limit(1)
            risk = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            raise exc.NoSuchRiskException()
        
        changes = {}
        for prop in props:
            value = props[prop]
            match prop:
                case 'checked':
                    if risk.is_checked != value:
                        before = risk.is_checked
                        risk.is_checked = value
                        changes[prop] = (before, value)
                case 'level':
                    if risk.level != value:
                        before = risk.level
                        risk.level = value
                        changes[prop] = (before, value)
                case 'reason_id':
                    if risk.reason_genre != value:
                        before = risk.reason_genre
                        risk.reason_genre = value
                        changes[prop] = (before, value)
                case 'remark':
                    if risk.remark != value:
                        before = risk.remark
                        risk.remark = value
                        changes[prop] = (before, value)
        
        if len(changes) == 0:
            return
        
        risk.updated_at = now
        
        checked = risk.is_checked
        level = risk.level
        reason_genre = risk.reason_genre
        remark = risk.remark
        created_at = risk.created_at
        updated_at = risk.updated_at

        await db_session.commit()

    await logging.write(ws,
    {
        'op': 'update_risk',
        'body': {
            'id': rid,
            'changes': changes
        }
    })
    
    msg = wsmsg.RiskUpdate(rid, checked, level, reason_genre, remark, created_at, updated_at).build()
    await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)

