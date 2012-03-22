"""
Author:  Thiago Marcos P. Santos
Created: August 28, 2008
Purpose: A signal/slot implementation
URL: http://code.activestate.com/recipes/576477/
Comment: Slightly modified with code from Patrick Chasco 
         (http://code.activestate.com/recipes/439356/) to support 
         connecting functions.
"""

from weakref import WeakValueDictionary
import inspect


class Signal(object):

    def __init__(self):
        self.__slots = WeakValueDictionary()

        # For keeping references to _FuncHost objects.
        self.__funchosts = {}

    def __call__(self, *args, **kargs):
        for key in self.__slots:
            func, _ = key
            func(self.__slots[key], *args, **kargs)

    def connect(self, slot):
        if inspect.ismethod(slot):
            key = (slot.im_func, id(slot.im_self))
            self.__slots[key] = slot.im_self
        else:
            host = _FuncHost(slot)
            self.connect(host.meth)
            # We stick a copy in here just to keep the instance alive.
            self.__funchosts[slot] = host

    def disconnect(self, slot):
        if inspect.ismethod(slot):
            key = (slot.im_func, id(slot.im_self))
            if key in self.__slots:
                self.__slots.pop(key)
        else:
            if slot in self.__funchosts:
                self.disconnect(self.__funchosts[slot].meth)
                self.__funchosts.pop(slot)

    def clear(self):
        self.__slots.clear()
        self.__funchosts.clear()


class _FuncHost(object):
    """Turn a function into a method."""
    def __init__(self, func):
        self.func = func

    def meth(self, *args, **kwargs):
        self.func(*args, **kwargs)


if __name__ == '__main__':
   
    a = 0
    def test_func():
        def foo():
            global a 
            a = a + 1
        global a
        a = 0
        s = Signal()
        s()
        s.connect(foo)
        s()
        s.disconnect(foo)
        s()        
        assert a == 1

    test_func()
