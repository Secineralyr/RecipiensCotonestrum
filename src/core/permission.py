from enum import IntEnum
from functools import wraps

from core import wsmsg


class Permission(IntEnum):
    USER = 0
    EMOJI_MODERATOR = 1
    MODERATOR = 2
    ADMINISTRATOR = 3


def require(level: Permission):
    def _require(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ws = args[0]
            if ws['level'] >= level:
                await func(*args, **kwargs)
            else:
                await send_denied(ws, level)
        return wrapper
    return _require


async def send_denied(ws, op, req_level):
    match req_level:
        case Permission.EMOJI_MODERATOR:
            text = "You must have at least 'Emoji Moderator' permission."
        case Permission.MODERATOR:
            text = "You must have at least 'Moderator' permission."
        case Permission.ADMINISTRATOR:
            text = "You must have at least 'Administrator' permission."
        case _:
            text = "Unknown error. This is server-side bug. Please report."
    msg = wsmsg.Denied(op, text).build()
    await ws.send(msg)
