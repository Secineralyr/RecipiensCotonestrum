import traceback

import asyncio
import websockets

from env import envs
from core import permission as perm
from core import exc
from core import wsmsg
from core.db import database

from front import websocket
from misskey import miapi, miws


HOST = envs['HOST']
PORT = int(envs['PORT'])


async def periodical_update_all_emojis(t):
    while True:
        try:
            await miapi.update_all_emojis()
        except exc.MiAPIErrorException as ex:
            traceback.print_exc()
            msg = wsmsg.MisskeyAPIError('internal', ex.err, '', 'periodical_update_all_emojis').build()
            await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)
        except exc.MiUnknownErrorException:
            traceback.print_exc('internal', 'periodical_update_all_emojis')
            msg = wsmsg.MisskeyUnknownError('internal', '', '').build()
            await websocket.broadcast(msg, require=perm.Permission.EMOJI_MODERATOR)
        except Exception:
            traceback.print_exc()
        await asyncio.sleep(t)


async def main():
    task_observe_emoji = asyncio.create_task(miws.observe_emoji_change())
    task_update_all_emojis = asyncio.create_task(periodical_update_all_emojis(3600))

    try:
        async with websockets.serve(websocket.connect, HOST, PORT):
            await asyncio.Future()  # run forever
    except KeyboardInterrupt:
        print('Exit server')

    task_observe_emoji.cancel()
    task_update_all_emojis.cancel()
    for connection in websocket.connections:
        connection['task_recv'].cancel()


if __name__ == '__main__':
    database.init()

    asyncio.run(main())


