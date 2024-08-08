from enum import IntEnum
from functools import wraps

from core import wsmsg


class Permission(IntEnum):
    NO_CREDENTIAL = -1
    USER = 0
    EMOJI_MODERATOR = 1
    MODERATOR = 2
    ADMINISTRATOR = 3

permission_levels = {}

def remove(ws):
    del permission_levels[ws]

def set_level(ws, level: Permission):
    permission_levels[ws] = level

def get_level(ws):
    return permission_levels[ws]

def require(op: str, level: Permission):
    def _require(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ws = args[0]
            if permission_levels[ws] >= level:
                await func(*args, **kwargs)
            else:
                await send_denied(ws, op, level)
        return wrapper
    return _require


async def send_denied(ws, op, req_level):
    match req_level:
        case Permission.USER:
            text = "You must have at least 'User' permission."
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
