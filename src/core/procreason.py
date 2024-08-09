import datetime

import sqlalchemy as sqla

from core import util
from core import logging
from core import permission as perm
from core import wsmsg
from core import exc
from core.db import database, model

from front import websocket


async def create_reason(text, ws=None):
    async with database.db_sessionmaker() as db_session:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
        rsid = util.randid()

        reason = model.Reason()
        reason.id = rsid
        reason.reason = text
        reason.created_at = now
        reason.updated_at = now

        db_session.add(reason)

        await db_session.commit()

    await logging.write(ws,
    {
        'op': 'create_reason',
        'body': {
            'id': rsid,
            'text': text
        }
    })

    msg = wsmsg.ReasonUpdated(rsid, text, now, now).build()
    await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)
    return rsid


async def update_reason(rsid, text, ws=None):
    changes = {}
    async with database.db_sessionmaker() as db_session:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        try:
            query = sqla.select(model.Reason).where(model.Reason.id == rsid).limit(1)
            reason = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            raise exc.NoSuchReasonException()

        if reason.reason == text:
            return

        before = reason.reason
        changes['reason'] = (before, text)

        reason.reason = text

        reason.updated_at = now

        created_at = reason.created_at

        await db_session.commit()

    await logging.write(ws,
    {
        'op': 'update_reason',
        'body': {
            'id': rsid,
            'changes': changes
        }
    })

    msg = wsmsg.ReasonUpdated(rsid, text, created_at, now).build()
    await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)

