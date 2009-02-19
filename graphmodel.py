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

class Graph(object):
    """Computes how a sound must be displayed on the screen.
    
    When an audio file is displayed on the screen, several frames are
    condensed in one column of pixels. This object computes what to display on
    the screen, according to zooming and position in the sound.

    """
    def __init__(self):
        self.changed = Signal()
        self._data = None
        self._view_start = 0
        self._view_end = 0
        self._width = 100

    def set_data(self, data):
        self._data = data
        self._view_start = 0
        self._view_end = len(self._data)
        self.changed()

    def view_starts_at(self, value):
        "Moves the view start and keep the view length"
        l = self._view_end - self._view_start
        self._view_start = value
        self._view_end = value + l
        self.changed()

    def get_info(self):
        "Returns information about the graph: length, view start, view end"
        length = len(self._data)
        start = self._view_start
        end = self._view_end
        return (length, start, end)

    def get_density(self):
        "Number of frames per pixel."
        return (self._view_end - self._view_start) / float(self._width)

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
        self._adjust_view()
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

    def _scroll(self, factor):
        """Shift the view.

        A negative factor shift the view to the left, a positive one
        to the right. The absolute value of the factor determines the
        length of the shift, relative to the view length. For example:
        0.1 is 10%, O.5 is one half, 1.0 is 100%.
        
        """
        l = self._view_end - self._view_start
        l = int(l * factor)
        self._view_start += l
        self._view_end += l
        self._adjust_view()
        self.changed()

    def scroll_left(self):
        self._scroll(-0.20)
            
    def scroll_right(self):
        self._scroll(0.20)

    def set_width(self, width):
        "Set the number of values the graph must have."
        self._width = int(width)
        self._adjust_view()
        self.changed()
        
    def get_values(self):
        "Return the graph values."
        width = self._width
        start, end = [int(round(v)) for v in self._view_start, self._view_end]
        visible = self._data[start:end]
        o = _overview(visible, width)
        return o

    def _adjust_view(self):
        """Adjust view boundaries.

        After scrolling or zooming, the view must be adjusted. Indeed,
        it must not start before 0 or end after the sound. Also, the
        view must contain enough values to fit in the width.

        """
        width = self._width

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


def test_overview():
    b = xrange(1000000000)
    print _overview(b, 30)
    
def test_Graph():
    c = Graph()
    c.set_data(range(1000))
    c.set_width(200)
    o = c.get_values()

    c = Graph()
    class Foo:
        def foo(self):
            print "Changed."
    f = Foo()
    c = Graph()
    c.changed.connect(f.foo)
    c.set_data(range(1000))

def test_zoom():
    data = [1, 2, 3, 4]
    g = Graph()
    g.set_data(data)

    g.set_width(4)
    g._zoom(point=1.5, factor=1)
    o = g.get_values()
    assert o == [1, 2, 3, 4]
    
    g._zoom(point=0, factor=1)
    o = g.get_values()
    assert o == [1, 2, 3, 4]

    g._zoom(point=6, factor=1)
    o = g.get_values()
    assert o == [1, 2, 3, 4]
    
    g.set_width(2)
    g.set_data(data)
    g._zoom(point=1.5, factor=0.5)
    o = g.get_values()
    assert o == [2, 3]

    g._zoom(point=1.5, factor=0.5)
    g.set_width(4)
    o = g.get_values()
    assert o == [1, 2, 3, 4]

    g.set_width(2)
    g._zoom(point=0, factor=0.5)
    o = g.get_values()
    assert o == [1, 2]

    g.set_width(4)
    g._zoom(point=0, factor=0.25)
    o = g.get_values()
    assert o == [1, 2, 3, 4]
    
    g.set_width(4)
    g._zoom(point=4, factor=4)
    o = g.get_values()
    assert o == [1, 2, 3, 4]


    g.set_width(3)
    data = [1, 2, 3, 4, 5]
    g.set_data(data)
    g._zoom(point=2, factor=0.5)
    o = g.get_values()
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
    g = Graph()
    g.set_data(data)

    g.set_width(2)
    g.zoom_in()
    o = g.get_values()
    assert o == [2, 3]

    g.zoom_out()
    g.set_width(4)
    o = g.get_values()
    assert o == [1, 2, 3, 4] 

def test_scroll():
    data = [1, 2, 3, 4]
    g = Graph()
    g.set_data(data)
    g.set_width(4)

    g.scroll_right()
    length, start, end = g.get_info()
    assert length == 4
    assert start == 0
    assert end == 4

    
if __name__ == "__main__":
    test_overview()
    test_Graph()
    test_zoom()
    test_zoom_in()
    test_scroll()
