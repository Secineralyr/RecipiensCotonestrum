import abc

import json

class IWSMessage(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def _build_json(self) -> dict:
        raise NotImplementedError()
    
    def build(self) -> str:
        return json.dumps(self._build_json())

class _EmojiData(IWSMessage):

    def __init__(self, eid, data, owner_id, risk_id, created_at, updated_at, misskey_id=None, name=None, category=None, tags=None, url=None, is_self_made=None, license=None):
        if data is not None:
            data_emoji = data

            self.misskey_id = data_emoji['id']
            self.name = data_emoji['name']
            self.category = data_emoji['category']
            self.tags = data_emoji['aliases']
            self.url = data_emoji['url']
            self.is_self_made = data_emoji['isSelfMadeResource']
            self.license = data_emoji['license']

        else:
            self.misskey_id = None
            self.name = None
            self.category = None
            self.tags = None
            self.url = None
            self.is_self_made = None
            self.license = None

        if misskey_id is not None: self.misskey_id = misskey_id
        if name is not None: self.name = name
        if category is not None: self.category = category
        if tags is not None: self.tags = tags
        if url is not None: self.url = url
        if is_self_made is not None: self.is_self_made = is_self_made
        if license is not None: self.license = license

        self.id = eid
        self.owner_id = owner_id
        self.risk_id = risk_id
        self.created_at = created_at
        self.updated_at = updated_at

    def _build_json(self) -> dict:
        return \
            {
                'id': self.id,
                'misskey_id': self.misskey_id,
                'name': self.name,
                'category': self.category,
                'tags': self.tags,
                'url': self.url,
                'is_self_made': self.is_self_made,
                'license': self.license,
                'owner_id': self.owner_id,
                'risk_id': self.risk_id,
                'created_at': self.created_at,
                'updated_at': self.updated_at
            }

class _UserData(IWSMessage):

    def __init__(self, uid, misskey_id, username):
        self.id = uid
        self.misskey_id = misskey_id
        self.username = username

    def _build_json(self) -> dict:
        return \
            {
                'id': self.id,
                'misskey_id': self.misskey_id,
                'username': self.username
            }

class _RiskData(IWSMessage):

    def __init__(self, rid, checked, level, reason_genre, remark, created_at, updated_at):
        self.id = rid
        self.checked = checked
        self.level = level
        self.reason_genre = reason_genre
        self.remark = remark
        self.created_at = created_at
        self.updated_at = updated_at

    def _build_json(self) -> dict:
        return \
            {
                'id': self.id,
                'checked': self.checked,
                'level': self.level,
                'reason_genre': self.reason_genre,
                'remark': self.remark,
                'created_at': self.created_at,
                'updated_at': self.updated_at
            }

class _ReasonData(IWSMessage):

    def __init__(self, rsid, text, created_at, updated_at):
        self.id = rsid
        self.text = text
        self.created_at = created_at
        self.updated_at = updated_at

    def _build_json(self) -> dict:
        return \
            {
                'id': self.id,
                'text': self.text,
                'created_at': self.created_at,
                'updated_at': self.updated_at
            }


class UserUpdate(IWSMessage):
    def __init__(self, uid, misskey_id, username):
        self.user = _UserData(uid, misskey_id, username)
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'user_update',
                'body': self.user._build_json()
            }

class UsersUpdate(IWSMessage):
    def __init__(self, users_data: list[_UserData]):
        self.users = users_data
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'users_update',
                'body': [u._build_json() for u in self.users]
            }

class EmojiUpdate(IWSMessage):
    def __init__(self, eid, data, owner_id, risk_id, created_at, updated_at, misskey_id=None, name=None, category=None, tags=None, url=None, is_self_made=None, license=None):
        self.emoji = _EmojiData(eid, data, owner_id, risk_id, created_at, updated_at, misskey_id, name, category, tags, url, is_self_made, license)
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'emoji_update',
                'body': self.emoji._build_json()
            }

class EmojisUpdate(IWSMessage):
    def __init__(self, emojis_data: list[_EmojiData]):
        self.emojis = emojis_data
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'emojis_update',
                'body': [e._build_json() for e in self.emojis]
            }

class EmojiDelete(IWSMessage):
    def __init__(self, eid: str):
        self.id = eid
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'emoji_delete',
                'body': {
                    'id': self.id
                }
            }

class EmojisDelete(IWSMessage):
    def __init__(self, eids: list[str]):
        self.ids = eids
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'emojis_delete',
                'body': {
                    'ids': self.ids
                }
            }

class RiskUpdate(IWSMessage):
    def __init__(self, rid, checked, level, reason_genre, remark, created_at, updated_at):
        self.risk = _RiskData(rid, checked, level, reason_genre, remark, created_at, updated_at)
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'risk_update',
                'body': self.risk._build_json()
            }

class RisksUpdate(IWSMessage):
    def __init__(self, risks_data: list[_RiskData]):
        self.risks = risks_data
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'risks_update',
                'body': [r._build_json() for r in self.risks]
            }

class ReasonUpdate(IWSMessage):
    def __init__(self, rsid, text, created_at, updated_at):
        self.reason = _ReasonData(rsid, text, created_at, updated_at)
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'reason_update',
                'body': self.reason._build_json()
            }

class ReasonsUpdate(IWSMessage):
    def __init__(self, reasons_data: list[_ReasonData]):
        self.reasons = reasons_data
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'reasons_update',
                'body': [rs._build_json() for rs in self.reasons]
            }

class ReasonDelete(IWSMessage):
    def __init__(self, rsid):
        self.id = rsid
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'reason_delete',
                'body': {
                    'id': self.id
                }
            }

class ReasonsDelete(IWSMessage):
    def __init__(self, rsids: list[str]):
        self.ids = rsids
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'reasons_delete',
                'body': {
                    'ids': self.ids
                }
            }


class OK(IWSMessage):
    def __init__(self, op: str, reqid: str, msg: str = ''):
        self.op = op
        self.reqid = reqid
        self.msg = msg
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'ok',
                'reqid': self.reqid,
                'body': {
                    'op': self.op,
                    'message': self.msg
                }
            }

class Denied(IWSMessage):
    def __init__(self, op: str, msg: str, reqid: str):
        self.op = op
        self.msg = msg
        self.reqid = reqid
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'denied',
                'reqid': self.reqid,
                'body': {
                    'op': self.op,
                    'message': self.msg
                }
            }

class MisskeyAPIError(IWSMessage):
    def __init__(self, op: str, mi_message: dict, reqid: str, error: str = ''):
        self.op = op
        self.mi_message = mi_message
        self.reqid = reqid
        self.error = error
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'misskey_api_error',
                'reqid': self.reqid,
                'body': {
                    'op': self.op,
                    'mi_message': self.mi_message,
                    'message': self.error
                }
            }

class MisskeyUnknownError(IWSMessage):
    def __init__(self, op: str, error: str, reqid: str):
        self.op = op
        self.reqid = reqid
        self.error = error
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'misskey_unknown_error',
                'reqid': self.reqid,
                'body': {
                    'op': self.op,
                    'message': self.error
                }
            }

class Error(IWSMessage):
    def __init__(self, op: str, error: str, reqid: str):
        self.op = op
        self.reqid = reqid
        self.error = error
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'error',
                'reqid': self.reqid,
                'body': {
                    'op': self.op,
                    'message': self.error
                }
            }

class InternalError(IWSMessage):
    def __init__(self, op: str, error: str, reqid: str):
        self.op = op
        self.reqid = reqid
        self.error = error
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'internal_error',
                'reqid': self.reqid,
                'body': {
                    'op': self.op,
                    'message': self.error
                }
            }
