import numpy

class Clipboard(object):
    # Borg pattern: http://code.activestate.com/recipes/66531/
    __shared_state = {"clip": numpy.array([])}
    def __init__(self):
        self.__dict__ = self.__shared_state

