from enum import IntEnum

import wsmsg

class Permission(IntEnum):
    USER = 0
    EMOJI_MODERATOR = 1
    MODERATOR = 2
    ADMINISTRATOR = 3

def require(level: Permission):
    def _require(func):
        async def wrapper(*args, **kwargs):
            ws = args[0]
            if ws['level'] >= level:
                await func(*args, **kwargs)
            else:
                await send_denied(ws, level)
        return wrapper
    return _require

async def send_denied(ws, req_level):
    msg = wsmsg.Denied(req_level).build()
    await ws.send(msg)
