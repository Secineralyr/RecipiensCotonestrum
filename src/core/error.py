from core import wsmsg


async def send_no_such_operation(ws, op):
    msg = wsmsg.Error(op, 'No such operation.').build()
    await ws.send(msg)
