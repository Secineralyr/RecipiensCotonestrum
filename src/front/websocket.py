import traceback

import json

import asyncio
import websockets

from core import permission as perm
from core import error

from front import receptor


connections = {}

async def broadcast(msg, exclude = None, require: perm.Permission = perm.Permission.USER):
    filtered_connections = {c for c in connections if c['level'] >= require}
    conns = set(filtered_connections) - {exclude,}
    websockets.broadcast(conns, msg)

def register(ws):
    task_recv = asyncio.create_task(reception(ws))
    connections[ws] = {'task_recv': task_recv, 'level': perm.Permission.NO_CREDENTIAL, 'uid': None}

def unregister(ws):
    connections[ws]['task_recv'].cancel()
    del connections[ws]

def get_uid(ws):
    return connections[ws]['uid']

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
                await error.send_no_such_operation(ws, op)
        except websockets.ConnectionClosed:
            break
