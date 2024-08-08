import json


class NoSuchRiskException(Exception):
    def __init__(self):
        pass


class MiAPIErrorException(Exception):
    def __init__(self, err: dict):
        self.err = err
    
    def __str__(self):
        return f'{json.dumps(self.err)}'

class MiUnknownErrorException(Exception):
    def __init__(self):
        pass

