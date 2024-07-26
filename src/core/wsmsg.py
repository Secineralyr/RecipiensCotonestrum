import abc

import json

from core import permission as perm

class IWSMessage(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def _build_json(self) -> dict:
        raise NotImplementedError()
    
    def build(self) -> str:
        return json.dumps(self._build_json())

class _EmojiData(IWSMessage):

    def __init__(self, eid, data, created_at, updated_at, misskey_id=None, name=None, category=None, tags=None, url=None, owner_mid=None, owner_name=None):
        if data is not None:
            data_emoji = data
            data_owner = data['user']

            self.misskey_id = data_emoji['id']
            self.name = data_emoji['name']
            self.category = data_emoji['category']
            self.tags = data_emoji['aliases']
            self.url = data_emoji['url']

            self.owner_mid = data_owner['id']
            self.owner_name = data_owner['username']
        else:
            self.misskey_id = None
            self.name = None
            self.category = None
            self.tags = None
            self.url = None

            self.owner_mid = None
            self.owner_name = None

        if misskey_id is not None: self.misskey_id = misskey_id
        if name is not None: self.name = name
        if category is not None: self.category = category
        if tags is not None: self.tags = tags
        if url is not None: self.url = url
        if owner_mid is not None: self.owner_mid = owner_mid
        if owner_name is not None: self.owner_name = owner_name

        self.id = eid
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
                'owner': {
                    'id': self.owner_mid,
                    'name': self.owner_name
                },
                'created_at': self.created_at,
                'updated_at': self.updated_at
            }


class EmojiUpdated(IWSMessage):
    def __init__(self, eid, data, created_at, updated_at, misskey_id=None, name=None, category=None, tags=None, url=None, owner_mid=None, owner_name=None):
        self.emoji = _EmojiData(eid, data, created_at, updated_at, misskey_id, name, category, tags, url, owner_mid, owner_name)
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'emoji_update',
                'body': self.emoji._build_json()
            }

class EmojiDeleted(IWSMessage):
    def __init__(self, eid):
        self.id = eid
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'emoji_delete',
                'body': {
                    'id': self.id
                }
            }

class Denied(IWSMessage):
    def __init__(self, op: str, required_level: perm.Permission):
        self.op = op
        match required_level:
            case perm.Permission.EMOJI_MODERATOR:
                self.msg = "You must have at least 'Emoji Moderator' permission."
            case perm.Permission.MODERATOR:
                self.msg = "You must have at least 'Moderator' permission."
            case perm.Permission.ADMINISTRATOR:
                self.msg = "You must have at least 'Administrator' permission."
            case _:
                self.msg = "Unknown error. This is server-side bug. Please report."
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'denied',
                'body': {
                    'op': self.op,
                    'message': self.msg
                }
            }

class MisskeyAPIError(IWSMessage):
    def __init__(self, op: str, mi_message: dict, error: str = ''):
        self.op = op
        self.error = error
        self.mi_message = mi_message
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'misskey_api_error',
                'body': {
                    'op': self.op,
                    'mi_message': self.mi_message,
                    'message': self.error
                }
            }

class MisskeyUnknownError(IWSMessage):
    def __init__(self, op: str, error: str):
        self.op = op
        self.error = error
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'misskey_unknown_error',
                'body': {
                    'op': self.op,
                    'message': self.error
                }
            }

class Error(IWSMessage):
    def __init__(self, op: str, error: str):
        self.op = op
        self.error = error
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'error',
                'body': {
                    'op': self.op,
                    'message': self.error
                }
            }
