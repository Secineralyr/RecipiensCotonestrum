from core import wsmsg


def internal_error(op, msg, reqid):
    return wsmsg.InternalError(op, msg, reqid).build()


def no_such_operation(op, reqid):
    return wsmsg.Error('internal', f'No such operation. (Name: {op})', reqid).build()

def no_such_emoji(op, eid, reqid):
    return wsmsg.Error(op, f'No such emoji. (ID: {eid})', reqid).build()

def no_such_user(op, uid, reqid):
    return wsmsg.Error(op, f'No such user. (ID: {uid})', reqid).build()

def no_such_risk(op, rid, reqid):
    return wsmsg.Error(op, f'No such risk data. (ID: {rid})', reqid).build()

def no_such_reason(op, rsid, reqid):
    return wsmsg.Error(op, f'No such reason data. (ID: {rsid})', reqid).build()
