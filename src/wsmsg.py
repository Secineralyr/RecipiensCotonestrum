import abc

import json

class IWSMessage(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def _build_json(self) -> dict:
        raise NotImplementedError()
    
    def build(self) -> str:
        return json.dumps(self._build_json())

class _EmojiData(IWSMessage):

    def __init__(self, eid, data, created_at, updated_at):
        data_emoji = data['emoji']
        data_owner = data['emoji']['user']

        self.id = eid
        self.misskey_id = data_emoji['id']
        self.name = data_emoji['name']
        self.category = data_emoji['category']
        self.tags = data_emoji['aliases']
        self.url = data_emoji['url']

        self.owner_mid = data_owner['id']
        self.owner_name = data_owner['username']

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
    def __init__(self, eid, data, created_at, updated_at):
        self.emoji = _EmojiData(eid, data, created_at, updated_at)
    
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
