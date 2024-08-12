from enum import IntEnum
from functools import wraps

from core import wsmsg


class Permission(IntEnum):
    NO_CREDENTIAL = -1
    USER = 0
    EMOJI_MODERATOR = 1
    MODERATOR = 2
    ADMINISTRATOR = 3

def get_name(level: Permission):
    match level:
        case Permission.NO_CREDENTIAL:
            return 'No credential'
        case Permission.USER:
            return 'User'
        case Permission.EMOJI_MODERATOR:
            return 'Emoji moderator'
        case Permission.MODERATOR:
            return 'Moderator'
        case Permission.ADMINISTRATOR:
            return 'Administrator'

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
            reqid = args[2]
            if permission_levels[ws] >= level:
                ret = await func(*args, **kwargs)
            else:
                ret = denied(op, level, reqid)
            return ret
        return wrapper
    return _require


def denied(op, req_level, reqid):
    if req_level > Permission.NO_CREDENTIAL and req_level >= Permission.ADMINISTRATOR:
        text = f"You must have at least '{get_name(req_level)}' permission."
    else:
        text = "Unknown error. This is server-side bug. Please report."
    return wsmsg.Denied(op, text, reqid).build()
