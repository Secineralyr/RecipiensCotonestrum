import aiohttp

from env import envs

from core import permission as perm
from core import procemoji

MISSKEY_HOST = envs['MISSKEY_HOST']
MISSKEY_TOKEN = envs['MISSKEY_TOKEN']

# for local-env test
NO_SSL = False
if 'NO_SSL' in envs:
    if envs['NO_SSL'] == '1':
        NO_SSL = True

if NO_SSL:
    HTTP_SCHEME = 'http'
    WS_SCHEME = 'ws'
else:
    HTTP_SCHEME = 'https'
    WS_SCHEME = 'wss'


async def authenticate(data):
    token = data['token']
    uri = f'{HTTP_SCHEME}://{MISSKEY_HOST}/api/i'
    async with aiohttp.ClientSession() as session:
        params = {'i': token}
        async with session.post(uri, json=params) as res:
            data = await res.json()
    if data['isAdmin']:
        level = perm.Permission.ADMINISTRATOR
    elif data['isModerator']:
        level = perm.Permission.MODERATOR
    elif data['isEmojiModerator']:
        level = perm.Permission.EMOJI_MODERATOR
    else:
        level = perm.Permission.USER
    return level

async def get_emoji_log(emoji_mid):
    uri = f'{HTTP_SCHEME}://{MISSKEY_HOST}/api/admin/emoji/get-emoji-log'
    async with aiohttp.ClientSession() as session:
        params = {'id': emoji_mid, 'i': MISSKEY_TOKEN}
        async with session.post(uri, json=params) as res:
            data = await res.json()
    return data

async def update_all_emojis():
    uri = f'{HTTP_SCHEME}://{MISSKEY_HOST}/api/admin/emoji/list'

    until = None
    async with aiohttp.ClientSession() as session:
        while True:
            params = {'limit': 100, 'i': MISSKEY_TOKEN}
            if until is not None:
                params['untilId'] = until
            async with session.post(uri, json=params) as res:
                data_emojis = await res.json()
                if len(data_emojis) == 0: break

                for data_emoji in data_emojis:
                    await procemoji.update_emoji(data_emoji)
                
                until = data_emojis[-1]['id']

