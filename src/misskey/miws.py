import traceback

import json

import websockets

from env import envs

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


async def observe_emoji_change():
    while True:
        uri = f'{WS_SCHEME}://{MISSKEY_HOST}/streaming?i={MISSKEY_TOKEN}'
        try:
            async with websockets.connect(uri) as ws:
                while True:
                    data = await ws.recv()
                    try:
                        print(data)
                        j = json.loads(data)
                        match j['type']:
                            case 'emojiAdded':
                                await procemoji.misskey_emoji_added(j['body'])
                            case 'emojiUpdated':
                                await procemoji.misskey_emojis_updated(j['body'])
                            case 'emojiDeleted':
                                await procemoji.misskey_emojis_deleted(j['body'])
                    except Exception:
                        traceback.print_exc()
        except websockets.ConnectionClosed:
            pass
        except Exception:
            traceback.print_exc()
