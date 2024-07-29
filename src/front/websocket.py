import traceback

import json

import asyncio
import websockets

from core import permission as perm
from core import wsmsg

from front import receptor


connections = {}

async def broadcast(msg, exclude=None):
    conns = set(connections) - {exclude,}
    websockets.broadcast(conns, msg)

def register(ws):
    task_recv = asyncio.create_task(reception(ws))
    connections[ws] = {'task_recv': task_recv, 'level': perm.Permission.USER}

def unregister(ws):
    connections[ws]['task_recv'].cancel()
    del connections[ws]

async def connect(ws, path):
    register(ws)
    print('websocket connection opened')
    try:
        await ws.wait_closed()
    except Exception:
        traceback.print_exc()
        ws.close()
    finally:
        print('websocket connection closed')
        unregister(ws)


receptors = receptor.receptors
async def reception(ws):
    while True:
        try:
            data = json.loads(await ws.recv())
            op = data['op']
            body = data['body']
            if op in receptors:
                await receptors[op](ws, body)
            else:
                msg = wsmsg.Error(op, 'No such operation.').build()
                await ws.send(msg)
        except websockets.ConnectionClosed:
            break
