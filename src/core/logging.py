import datetime
import json

from core.db import database, model

from front import websocket


# When ws = None, operator is 'System'
# otherwise operator is user (from ws data).
async def write(ws, data: dict):
    async with database.db_sessionmaker() as db_session:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

        log = model.Log()
        if ws is None:
            log.operator = None
        else:
            log.operator = websocket.get_uid(ws)
        log.text = json.dumps(data)
        log.created_at = now

        db_session.add(log)
        await db_session.commit()
