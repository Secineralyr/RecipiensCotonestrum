import traceback

import json

import websockets

from env import envs

from core import permission as perm
from core import procemoji
from core import wsmsg
from core import exc

from front import websocket


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
                        j = json.loads(data)
                        match j['type']:
                            case 'emojiAdded':
                                await procemoji.misskey_emoji_added(j['body'])
                            case 'emojiUpdated':
                                await procemoji.misskey_emojis_updated(j['body'])
                            case 'emojiDeleted':
                                await procemoji.misskey_emojis_deleted(j['body'])
                    except exc.MiAPIErrorException as ex:
                        traceback.print_exc()
                        msg = wsmsg.MisskeyAPIError('internal', ex.err, '', f'observe_emoji_change type: {j["type"]}').build()
                        await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)
                    except exc.MiUnknownErrorException:
                        traceback.print_exc()
                        msg = wsmsg.MisskeyUnknownError('internal', f'observe_emoji_change type: {j["type"]}').build()
                        await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)
                    except Exception:
                        traceback.print_exc()
        except websockets.ConnectionClosed:
            pass
        except Exception:
            traceback.print_exc()
