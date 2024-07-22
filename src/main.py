import os

import asyncio
import websockets

from env import envs

from front import websocket
from misskey import miapi, miws


HOST = envs['HOST']
PORT = int(envs['PORT'])


async def periodical_update_all_emojis(t):
    while True:
        await asyncio.sleep(t)
        await miapi.update_all_emojis()


async def main():
    await miapi.update_all_emojis()

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
    asyncio.run(main())


