# Gum sound editor (https://github.com/stackp/Gum)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from gum.lib.event import Signal
try:
    from gum import fast
except ImportError:
    HAVE_FAST = False
    print "Warning: 'fast' module not found. You won't have fast display!"
else:
    HAVE_FAST = True

def frame2cell(frame, density):
    return frame / float(density)

def cell2frame(cell, density):
    return cell * density

def _overview(data, start, width, density):
    numchan = data.ndim
    if numchan == 1:
        channels = [data]
    else:
        channels = data.transpose()
    o = []
    for chan in channels:
        values = _condense(chan, start, width, density)
        o.append(values)
    return o

def _condense(data, start, width, density):
    """Returns a list of (min, max) tuples.

    A density slices the data in "cells", each cell containing several
    frames. This function returns the min and max of each visible cell.

    """
    res = []
    start = int(start)
    width = int(width)
    for i in range(start, start + width):
        a = cell2frame(i, density)
        b = cell2frame(i + 1, density)
        d = data[a:b]
        if len(d) == 0:
            break
        mini = d.min()
        maxi = d.max()
        res.append((mini, maxi))
    return res

if HAVE_FAST:
    _condense = fast._condense


def intersection((a, b), (x, y)):
    if b <= x or a >= y:
        return None
    else:
        start = max(a, x)
        end = min(b, y)
        return start, end

class OverviewCache(object):

    def set_data(self, data):
        self._data = data
        # _cache is a tuple (start_index, width, density, values)
        self._cache = None, None, None, None

    def get(self, start, width, density):
        start = int(start)
        done = False
        c_start, c_width, c_density, _ = self._cache

        # Same as last call
        if (c_start, c_width, c_density) == (start, width, density):
            done = True

        # There is an intersection
        if not done and c_density == density:
            inter = intersection((start, start + width),
                                 (c_start, c_start + c_width))
            if inter != None:
                head, tail = [], []
                a, b = inter
                if start < a:
                    head = _overview(self._data, start, a - start, density)
                if b < start + width:
                    tail = _overview(self._data, b, start + width - b, density)
                i, j = [int(x - c_start) for x in inter]
                body = zip(*self._cache[3])[i:j]
                ov = zip(*head) + body + zip(*tail)
                ov = zip(*ov)
                ov = [list(t) for t in ov]
                self._cache = (start, width, density, ov)
                done = True

        # Compute entirely
        if not done:
            ov = _overview(self._data, start, width, density)
            self._cache = (start, width, density, ov)

        return self._cache[3]


class Graph(object):
    """Scale the sound visualization.
    
    When audio is drawn on the screen, several frames are condensed in
    one column of pixels. This object computes what to display,
    according to zooming and position in the sound.

    """
    def __init__(self, sound):
        self.changed = Signal()
        self._overview = OverviewCache()
        self._width = 100.
        self.set_sound(sound)

    def get_density(self):
        return self._density

    def set_density(self, value):
        mini = 1
        maxi = max(mini, self.numframes() / float(self._width))
        self._density = self._gauge(value, mini, maxi)

    density = property(get_density, set_density)

    def set_sound(self, sound):
        self._sound = sound
        self._view_start = 0 # is a cell
        self.density = self.numframes() / float(self._width)
        self._sound.changed.connect(self.on_sound_changed)
        self.on_sound_changed()

    def on_sound_changed(self):
        self._overview.set_data(self._sound.frames)
        self.update()

    def set_width(self, width):
        start, end = self.view()
        self._width = width
        self.density = (end - start) / float(width)
        self.move_to(start)

    def update(self):
        self._adjust_view()
        self.changed()

    def numframes(self):
        return len(self._sound.frames)
    
    def view(self):
        """
        Return start and end frames; end is exclusive.
        """
        start = cell2frame(self._view_start, self.density)
        end = start + cell2frame(self._width, self.density)
        n = self.numframes()
        if end > n:
            end = n
        return (start, end)

    def set_view(self, start, end):
        self.density = (end - start)  / float(self._width)
        self.move_to(start)

    def move_to(self, frame):
        "Moves the view start and keep the view length"
        self._view_start = frame2cell(frame, self.density)
        self.update()

    def center_on(self, frame):
        self.move_to(frame - (self._width - 1) * self.density * 0.5)

    def frmtopxl(self, f):
        "Converts a frame index to a pixel index."
        return int(frame2cell(f, self.density) - self._view_start)

    def pxltofrm(self, p):
        "Converts a pixel index to a frame index."
        f = cell2frame(self._view_start + p, self.density)
        return self._gauge(f, 0, self.numframes())
    
    def _gauge(self, value, mini, maxi):
        "Calibrate value between mini and maxi."
        if value < mini:
            value = mini
        if value > maxi:
            value = maxi
        return value

    def _zoom(self, factor):
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
        self.density *= factor
        
    def middle(self):
        start, end = self.view()
        return start + (end - 1 - start) * 0.5

    def zoom_in(self):
        "Make view twice smaller, centering on the middle of the view."
        mid = self.middle()
        self._zoom(0.5)
        self.center_on(mid)

    def zoom_out(self):
        "Make view twice larger, centering on the middle of the view."
        mid = self.middle()
        self._zoom(2)
        self.center_on(mid)

    def zoom_out_full(self):
        "Fit everything in the view."
        self.set_view(0, self.numframes())

    def is_zoomed_out_full(self):
        start, end = self.view()
        return start == 0 and end == self.numframes()

    def zoom_on(self, pixel, factor):
        point = self.pxltofrm(pixel)
        self._zoom(factor)
        self.move_to(point - pixel * self.density)

    def zoom_in_on(self, pixel):
        self.zoom_on(pixel, 0.8)

    def zoom_out_on(self, pixel):
        self.zoom_on(pixel, 1.2)

    def _scroll(self, factor):
        """Shift the view.

        A negative factor shifts the view to the left, a positive one
        to the right. The absolute value of the factor determines the
        length of the shift, relative to the view length. For example:
        0.1 is 10%, 0.5 is one half, 1.0 is 100%.
        
        """
        l = self._width * factor
        self._view_start += l
        self.update()

    def scroll_left(self):
        self._scroll(-0.1)
            
    def scroll_right(self):
        self._scroll(0.1)

    def channels(self):
        "Return the graph values."
        o = self._overview.get(self._view_start, self._width, self.density)
        return o

    def _adjust_view(self):
        numcells = frame2cell(self.numframes(), self.density)
        if  self._view_start + self._width > numcells:
            self._view_start = numcells - self._width
        if self._view_start < 0:
            self._view_start = 0

# Test functions

DTYPE = 'float64'

def test_overview():
    import numpy
    l = 1000000
    b = numpy.array(range(l), DTYPE)
    assert len(_condense(b, 0, l, l/10)) == 10
    assert len(_condense(b, 0, l, l/100)) == 100

def test_middle():
    from gum.lib.mock import Mock, Fake
    import numpy
    sound = Mock({"numchan": 1})
    sound.changed = Fake()
    sound.frames = []
    g = Graph(sound)
    for nframes, mid in [(4, 1.5), (9, 4), (10, 4.5)]:
        sound.frames = numpy.array(range(nframes))
        g.set_sound(sound)
        assert g.middle() == mid

def test_intersection():
    assert intersection((1, 4), (2, 3)) == (2, 3)
    assert intersection((2, 3), (1, 4)) == (2, 3)
    assert intersection((1, 7), (5, 9)) == (5, 7)
    assert intersection((5, 9), (1, 7)) == (5, 7)
    assert intersection((1, 4), (5, 9)) == None
    assert intersection((5, 9), (1, 4)) == None

def test_Graph():
    from gum.lib.mock import Mock, Fake
    import numpy
    
    sound = Mock({"numchan": 1})
    sound.changed = Fake()
    sound.frames = numpy.array(range(1000), DTYPE)

    c = Graph(sound)
    c.set_width(200)
    o = c.channels()

    class Foo:
        def foo(self):
            print "Changed."
    f = Foo()
    c = Graph(sound)
    c.changed.connect(f.foo)
    c.set_width(200)
    o = c.channels()

    # stereo
    import numpy
    sound = Mock({"numchan": 2})
    sound.changed = Fake()
    data = numpy.array([[1, 1], [2, 2], [3, 3]], DTYPE)
    sound.frames = data
    c = Graph(sound)
    o = c.channels()
    assert(len(o)) == 2
    

def test_zoom():
    from gum.lib.mock import Mock, Fake
    import numpy

    sound = Mock({"numchan": 1})
    data = numpy.array([1, 2, 3, 4], DTYPE)
    sound.frames = data
    sound.changed = Fake()

    g = Graph(sound)

    g.set_width(4)
    g._zoom(1)
    g.center_on(1.5)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]
    
    g._zoom(factor=1)
    g.center_on(0)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

    g._zoom(1)
    g.center_on(6)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]
    
    g._zoom(factor=0.5)
    g.center_on(1.5)
    g.set_width(4)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

    g.set_width(2)
    g._zoom(0.5)
    g.center_on(0)
    o = g.channels()
    assert o == [[(1, 1), (2, 2)]]

    g.set_width(4)
    g._zoom(0.25)
    g.center_on(0)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]
    
    g.set_width(4)
    g._zoom(4)
    g.center_on(4)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]], o

    g.set_width(100)
    data = numpy.array(range(3241))
    sound.frames = data
    g.zoom_out_full()
    g._zoom(factor=0.5)
    g._zoom(factor=0.5)
    start, end = g.view()
    g.zoom_out_full()    
    g._zoom(factor=0.5 * 0.5)
    assert (start, end) == g.view()

def test_zoom_in():
    import numpy 
    from gum.lib.mock import Mock, Fake
    sound = Mock({"numchan": 1})
    sound.changed = Fake()

    data = numpy.array([1, 2, 3, 4], DTYPE)
    sound.frames = data
    g = Graph(sound)

    g.set_width(2)
    g.zoom_in()
    o = g.channels()
    assert o == [[(2, 2), (3, 3)]]

    g.zoom_out()
    g.set_width(4)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

def test_zoom_in_on():
    import numpy
    from gum.lib.mock import Mock, Fake
    sound = Mock({"numchan": 1})
    sound.changed = Fake()
    data = numpy.array([1, 2, 3, 4], DTYPE)
    sound.frames = data
    g = Graph(sound)
    g.set_width(2)

    g.zoom_in_on(0)
    assert g.channels() == [[(1, 2), (3, 3)]]

    g.zoom_out()
    g.zoom_in_on(1)
    assert g.channels() == [[(1, 2), (3, 3)]]

    g.zoom_out()
    g.zoom_in_on(2)
    assert g.channels() == [[(1, 2), (3, 3)]]

def test_scroll():
    import numpy
    from gum.lib.mock import Mock, Fake

    sound = Mock({})
    data = numpy.array([1, 2, 3, 4])
    sound.frames = data
    sound.changed = Fake()

    g = Graph(sound)
    g.set_width(4)

    g.scroll_right()
    length = g.numframes()
    start, end = g.view()
    assert length == 4
    assert start == 0
    assert end == 4

def test_density():
    from gum.models import Sound
    import gum
    g = Graph(Sound(gum.basedir + "/data/test/test1.wav"))
    g.set_width(700)
    g.zoom_in()
    g.channels()
    g.zoom_in()
    g.channels()
    g.zoom_in()
    d = g.density

    pos = [26744.9875, 18793.775, 15902.425, 13011.075, 10119.725, 7228.375,
           4337.025, 1445.675, 0.0, 2891.35, 5782.7, 8674.05, 11565.4,
           14456.75, 17348.1, 20239.45]

    for x in pos:
        g.move_to(x)
        assert d == g.density

def test_channels():
    import numpy
    from gum.lib.mock import Mock, Fake
    sound = Mock({"numchan": 1})
    sound.changed = Fake()
    sound.frames = numpy.array(range(1000000), DTYPE)
    g = Graph(sound)

    for w in [1, 10, 11, 12, 13, 14, 15, 29, 54, 12.0, 347, 231., 1030]:
        g.set_width(w)
        c = g.channels()
        assert len(c[0]) == w, \
             "expected: %d, got: %d, density: %f, last value: %s " % \
                                     (w, len(c[0]), g.density, str(c[0][-1]))

def test_OverviewCache():
    import numpy
    
    cache = OverviewCache()
    cache.set_data(numpy.array([1, 2, 3, 4], DTYPE))
    o = cache.get(start=0, width=4, density=1)
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

    o2 = cache.get(start=0, width=4, density=1)
    assert o2 == o
    assert o2 is o

    cache.set_data(numpy.array([1, 2, 3, 4], DTYPE))
    o3 = cache.get(start=0, width=4, density=1)
    assert o3 == o
    assert o3 is not o

    cache.set_data(numpy.array(range(1000), DTYPE))
    o1 = cache.get(start=0, width=10, density=10)
    o2 = cache.get(start=4, width=10, density=10)
    o3 = cache.get(start=0, width=10, density=10)
    o4 = cache.get(start=4, width=10, density=10)
    assert o1 == o3
    assert o2 == o4
    assert o1[0][4:] == o2[0][:6], str(o1[0][4:]) + str(o2[0][:6])


if __name__ == "__main__":
    test_overview()
    test_Graph()
    test_intersection()
    test_channels()
    test_middle()
    test_zoom()
    test_zoom_in()
    test_scroll()
    test_zoom_in_on()
    test_OverviewCache()
    test_density()
