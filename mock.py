import types

class Mock(object):

    def __init__(self, dico):
        for name, result in dico.items():
            m = self._make_method(name, result)
            setattr(self, name, m)
            
    def _make_method(self, name, result):
        def func(self, *args, **kwargs):
            return result
        
        method = types.MethodType(func, name)
        return method


class Fake(object):

    def _method(self, *args, **kwargs):
        print "hello"
        return []

    def __getattr__(self, a):
        if a not in self.__dict__:
            return self._method


if __name__ == "__main__":
    m = Mock({"one": 1, "zero": 0})
    assert m.one() == 1
    assert m.one("bla") == 1
    assert m.zero() == 0

    f = Fake()
    f.foo()
    f.bar()
