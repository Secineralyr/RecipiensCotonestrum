import traceback

import json

import asyncio
import websockets

from core import permission as perm
from core import error
from core import wsmsg

from front import receptor


connections = {}

async def broadcast(msg, exclude = None, require: perm.Permission = perm.Permission.USER):
    filtered_connections = {c for c in connections if perm.get_level(c) >= require}
    conns = set(filtered_connections) - {exclude,}
    websockets.broadcast(conns, msg)

def register(ws):
    task_recv = asyncio.create_task(reception(ws))
    connections[ws] = {'task_recv': task_recv, 'uid': None}
    perm.set_level(ws, perm.Permission.NO_CREDENTIAL)

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
        await ws.close()
    finally:
        print('websocket connection closed')
        unregister(ws)


receptors = receptor.receptors
async def reception(ws):
    while True:
        try:
            data = json.loads(await ws.recv())
            op = data['op']
            reqid = data['reqid']
            body = data['body']
            if op in receptors:
                msg = await receptors[op](ws, body, reqid)
            else:
                msg = error.no_such_operation(op, reqid)
            await ws.send(msg)
        except asyncio.exceptions.CancelledError:
            await ws.close()
            break
        except websockets.ConnectionClosed:
            break
        except:
            traceback.print_exc()
            msg = error.internal_error(op, 'Internal error occured. Please report.', reqid)
            await ws.send(msg)
