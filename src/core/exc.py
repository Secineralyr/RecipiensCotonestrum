import json


class NoSuchRiskException(Exception):
    def __init__(self):
        super.__init__()


class MiAPIErrorException(Exception):
    def __init__(self, err: dict):
        super.__init__()
        self.err = err
    
    def __str__(self):
        return f'{json.dumps(self.err)}'

class MiUnknownErrorException(Exception):
    def __init__(self):
        super.__init__()

