from event import Signal

def _overview(data, width):
    density = len(data) / float(width)
    if density < 1:
        density = 1
    left = 0
    end = len(data)
    res = []
    while int(round(left)) < end:
        i = int(round(left))
        res.append(data[i])
        left = left + density 
    return res

class GraphData(object):

    def __init__(self):
        self.changed = Signal()
        self._data = None
        self._view_start = 0
        self._view_end = 0

    def set_data(self, data):
        self._data = data
        self._view_start = 0
        self._view_end = len(self._data)
        self.changed()

    def scroll_left(self):
        pass

    def scroll_right(self):
        pass

    def zoom_in(self):
        pass

    def zoom_out(self):
        pass

    def get_info(self, width):
        width = int(width)
        visible = self._data[self._view_start:self._view_end]
        o = _overview(visible, width)
        return o

def test_overview():
    b = xrange(1000000000)
    print _overview(b, 30)
    
def test_GraphData():
    c = GraphData()
    c.set_data(range(1000))
    o = c.get_info(200)

    c = GraphData()
    class Foo:
        def foo(self):
            print "Changed."
    f = Foo()
    c = GraphData()
    c.changed.connect(f.foo)
    c.set_data(range(1000))
    

if __name__ == "__main__":
    test_overview()
    test_GraphData()

