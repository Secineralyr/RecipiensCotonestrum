from core import wsmsg


def internal_error(op, msg):
    return wsmsg.InternalError(op, msg).build()


def no_such_operation(op):
    return wsmsg.Error('internal', f'No such operation. (Name: {op})').build()

def no_such_emoji(op, eid):
    return wsmsg.Error(op, f'No such emoji. (ID: {eid})').build()

def no_such_user(op, uid):
    return wsmsg.Error(op, f'No such user. (ID: {uid})').build()

def no_such_risk(op, rid):
    return wsmsg.Error(op, f'No such risk data. (ID: {rid})').build()

def no_such_reason(op, rsid):
    return wsmsg.Error(op, f'No such reason data. (ID: {rsid})').build()
