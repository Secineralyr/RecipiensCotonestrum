from core import wsmsg


async def send_internal_error(ws, op, msg):
    msg = wsmsg.InternalError(op, msg).build()
    await ws.send(msg)


async def send_no_such_operation(ws, op):
    msg = wsmsg.Error('internal', f'No such operation. (Name: {op})').build()
    await ws.send(msg)

async def send_no_such_emoji(ws, op, eid):
    msg = wsmsg.Error(op, f'No such emoji. (ID: {eid})').build()
    await ws.send(msg)

async def send_no_such_risk(ws, op, rid):
    msg = wsmsg.Error(op, f'No such risk data. (ID: {rid})').build()
    await ws.send(msg)
