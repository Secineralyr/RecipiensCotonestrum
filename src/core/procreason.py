import datetime

import sqlalchemy as sqla

from core import util
from core import wsmsg
from core import exc
from core.db import database, model

from front import websocket


async def create_reason(text):
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

    msg = wsmsg.ReasonUpdated(rsid, text, now, now).build()
    await websocket.broadcast(msg)
    return rsid


async def edit_reason(rsid, text):
    async with database.db_sessionmaker() as db_session:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        try:
            query = sqla.select(model.Reason).where(model.Reason.id == rsid).limit(1)
            reason = (await db_session.execute(query)).one()[0]
        except sqla.exc.NoResultFound:
            raise exc.NoSuchRiskException()

        if reason.reason == text:
            return

        reason.reason = text

        reason.updated_at = now

        created_at = reason.created_at

        await db_session.commit()

    msg = wsmsg.ReasonUpdated(rsid, text, created_at, now).build()
    await websocket.broadcast(msg)
