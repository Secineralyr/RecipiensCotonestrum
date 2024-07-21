import abc

import json

import permission

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
    def __init__(self, required_level):
        match required_level:
            case 1:
                self.msg = "You must have at least 'Emoji Moderator' permission."
            case 2:
                self.msg = "You must have at least 'Moderator' permission."
            case 3:
                self.msg = "You must have at least 'Administrator' permission."
            case _:
                self.msg = "Unknown error. This is server-side bug. Please report."
    
    def _build_json(self) -> dict:
        return \
            {
                'op': 'denied',
                'body': {
                    'message': self.msg
                }
            }
