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

    def _zoom(self, point, factor):
        """Expand or shrink view according to factor.

        0 < factor < 1     zoom in
            factor = 1     unchanged
        1 < factor < +Inf  zoom out

        The zoom factor is relative to the current zoom, ie.::

            self._zoom(x, n)
            self._zoom(x, m)

        is equivalent to::

            self._zoom(x, n * m)
        
        """
        l = self._view_end - self._view_start
        l = l * factor
        self._view_start = point - l * 0.5
        self._view_end = point + l * 0.5
        self.changed()

        
    def zoom_in(self):
        "Make view twice smaller, centering on the middle of the view."
        mid = self._view_start + (self._view_end - self._view_start) * 0.5
        self._zoom(mid, 0.5)
        
    def zoom_out(self):
        "Make view twice larger, centering on the middle of the view."
        mid = self._view_start + (self._view_end - self._view_start) * 0.5 
        self._zoom(mid, 2)

    def zoom_fit(self):
        "Fit everything in the view."
        self._view_start = 0
        self._view_end = len(self._data)
        self.changed()

    def get_info(self, width):
        width = int(width)

        # When the zoom is too strong and the width cannot be filled,
        # zoom out.
        view_length = self._view_end - self._view_start
        if view_length < width:
            self._view_start -= (width - view_length) * 0.5
            self._view_end = self._view_start + width

        # Check and adjust visible bounds.
        if self._view_start < 0:
            self._view_end += -self._view_start 
            self._view_start = 0
        elif self._view_end > len(self._data):
            self._view_start -= (self._view_end - len(self._data))
            self._view_end = len(self._data)

        # Ultimate check on bounds.
        if self._view_start < 0:
            self._view_start = 0
        if self._view_end > len(self._data):
            self._view_end = len(self._data)
            
        start, end = [int(round(v)) for v in self._view_start, self._view_end]
        visible = self._data[start:end]
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

def test_zoom():
    data = [1, 2, 3, 4]
    g = GraphData()
    g.set_data(data)

    g._zoom(point=1.5, factor=1)
    o = g.get_info(4)
    assert o == [1, 2, 3, 4]
    
    g._zoom(point=0, factor=1)
    o = g.get_info(4)
    assert o == [1, 2, 3, 4]

    g._zoom(point=6, factor=1)
    o = g.get_info(4)
    assert o == [1, 2, 3, 4]
    
    g.set_data(data)
    g._zoom(point=1.5, factor=0.5)
    o = g.get_info(2)
    assert o == [2, 3]

    g._zoom(point=1.5, factor=0.5)
    o = g.get_info(4)
    assert o == [1, 2, 3, 4]

    g._zoom(point=0, factor=0.5)
    o = g.get_info(2)
    assert o == [1, 2]

    g._zoom(point=0, factor=0.25)
    o = g.get_info(4)
    assert o == [1, 2, 3, 4]
    
    g._zoom(point=4, factor=4)
    o = g.get_info(4)
    assert o == [1, 2, 3, 4]


    data = [1, 2, 3, 4, 5]
    g.set_data(data)
    g._zoom(point=2, factor=0.5)
    o = g.get_info(3)
    assert o == [2, 3, 4]

    data = [1, 2, 3, 4, 5]
    g.set_data(data)
    g._zoom(point=2, factor=0.5)
    g._zoom(point=2, factor=0.5)
    start, end = g._view_start, g._view_end
    
    data = [1, 2, 3, 4, 5]
    g.set_data(data)
    g._zoom(point=2, factor=0.5 * 0.5)
    assert (start, end) == (g._view_start, g._view_end)

def test_zoom_in():
    data = [1, 2, 3, 4]
    g = GraphData()
    g.set_data(data)

    g.zoom_in()
    o = g.get_info(2)
    assert o == [2, 3]

    g.zoom_out()
    o = g.get_info(4)
    assert o == [1, 2, 3, 4] 
    
if __name__ == "__main__":
    test_overview()
    test_GraphData()
    test_zoom()
    test_zoom_in()
