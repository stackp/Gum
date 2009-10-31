# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from event import Signal

def _cell_start(frame, density):
    """Return the first frame of the cell in which `frame` belongs."""
    return round(frame / density) * density

def _overview(data, start, end, density):
    start = _cell_start(start, density)
    numchan = data.ndim
    if numchan == 1:
        channels = [data]
    else:
        channels = data.transpose()
    o = []
    for chan in channels:
        values = _condense(chan[start:end], density)
        o.append(values)
    return o

def _condense(data, density):
    """Returns a list of (min, max) tuples.

    A density slices the data in "cells", each cell containing several
    frames. This function returns the min and max of each visible cell.

    """
    left = 0
    end = len(data)
    res = []
    while round(left) < end:
        right = left + density
        i = int(round(left))
        j = int(round(right))
        d = data[i:j]
        mini = d.min()
        maxi = d.max()
        res.append((mini, maxi))
        left = right
    return res


class OverviewCache(object):

    def set_data(self, data):
        self._data = data
        # _cache is a tuple (start_index, end_index, density, values)
        self._cache = None, None, None, None

    def get(self, start, end, density):
        c_start, c_end, c_density, _ = self._cache
        if (c_start, c_end, c_density) != (start, end, density):
            ov = _overview(self._data, start, end, density)
            self._cache = (start, end, density, ov)

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
        self._width = 100
        self.set_sound(sound)

    def set_sound(self, sound):
        self._sound = sound
        self._view_start = 0
        self._view_end = len(self._sound.frames)
        self._sound.changed.connect(self.on_sound_changed)
        self.on_sound_changed()

    def on_sound_changed(self):
        self._overview.set_data(self._sound.frames)
        self.update()

    def update(self):
        self._adjust_view()
        self.changed()

    def set_view(self, start, end):
        self._view_start = start
        self._view_end = end
        self.update()

    def move_to(self, frame):
        "Moves the view start and keep the view length"
        l = self._view_end - self._view_start
        self.set_view(frame, frame + l)

    def center_on(self, frame):
        l = self._view_end - self._view_start
        self.set_view(frame - l * 0.5 + 0.5, frame + l * 0.5 + 0.5)

    def numframes(self):
        return len(self._sound.frames)
    
    def view(self):
        start = self._view_start
        end = self._view_end
        return (start, end)

    def density(self):
        "Number of frames per pixel."
        number_frames_view = self._view_end - self._view_start
        d = float(number_frames_view) / self._width
        # Round to disregard inacurracy of floating point operations,
        # as shown in the test_density() function.
        d = round(d, 10)
        if d < 1:
            d = 1.
        return d

    def frmtopxl(self, f):
        "Converts a frame index to a pixel index."
        p = int(round(f - self._view_start) / self.density())
        return p

    def pxltofrm(self, p):
        "Converts a pixel index to a frame index."
        f = int(round(self._view_start + p * self.density()))
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
        l = self._view_end - self._view_start
        l = l * factor
        self._view_end = self._view_start + l
        
    def middle(self):
        start, end = self._view_start, self._view_end
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
        self.set_view(0, len(self._sound.frames))

    def is_zoomed_out_full(self):
        start, end = self.view()
        return start == 0 and end == len(self._sound.frames)

    def zoom_in_on(self, pixel):
        point = self.pxltofrm(pixel)
        self.zoom_in()
        self.move_to(point - pixel * self.density())

    def zoom_out_on(self, pixel):
        point = self.pxltofrm(pixel)
        self.zoom_out()
        self.move_to(point - pixel * self.density())

    def _scroll(self, factor):
        """Shift the view.

        A negative factor shifts the view to the left, a positive one
        to the right. The absolute value of the factor determines the
        length of the shift, relative to the view length. For example:
        0.1 is 10%, O.5 is one half, 1.0 is 100%.
        
        """
        l = self._view_end - self._view_start
        l = int(l * factor)
        self.set_view(self._view_start + l, self._view_end + l)

    def scroll_left(self):
        self._scroll(-0.20)
            
    def scroll_right(self):
        self._scroll(0.20)

    def set_width(self, width):
        "Set the number of values the graph must have."
        self._width = int(width)
        self.update()
        
    def channels(self):
        "Return the graph values."
        o = self._overview.get(self._view_start, self._view_end,self.density())
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
        elif self._view_end > len(self._sound.frames):
            self._view_start -= (self._view_end - len(self._sound.frames))
            self._view_end = len(self._sound.frames)

        # Ultimate check on bounds.
        if self._view_start < 0:
            self._view_start = 0
        if self._view_end > len(self._sound.frames):
            self._view_end = len(self._sound.frames)


def test_overview():
    import numpy
    b = numpy.array(range(1000000))
    assert len(_condense(b, 100000)) == 10
    assert len(_condense(b, 10000)) == 100

def test_middle():
    from mock import Mock, Fake
    import numpy
    sound = Mock({"numchan": 1})
    sound.changed = Fake()
    sound.frames = []
    g = Graph(sound)
    for nframes, mid in [(4, 1.5), (9, 4), (10, 4.5)]:
        sound.frames = numpy.array(range(nframes))
        g.set_sound(sound)
        assert g.middle() == mid

def test_Graph():
    from mock import Mock, Fake
    import numpy
    
    sound = Mock({"numchan": 1})
    sound.changed = Fake()
    sound.frames = numpy.array(range(1000))

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
    data = numpy.array([[1, 1], [2, 2], [3, 3]])
    sound.frames = data
    c = Graph(sound)
    o = c.channels()
    assert(len(o)) == 2
    

def test_zoom():
    from mock import Mock, Fake
    import numpy

    sound = Mock({"numchan": 1})
    data = numpy.array([1, 2, 3, 4])
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
    
    g.set_width(2)
    g._zoom(0.5)
    g.center_on(1.5)
    o = g.channels()
    assert o == [[(2, 2), (3, 3)]]

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
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

    g.set_width(3)
    data = numpy.array([1, 2, 3, 4, 5])
    sound.frames = data
    g._zoom(0.5)
    g.center_on(2)
    o = g.channels()
    assert o == [[(2, 2), (3, 3), (4, 4)]]

    g._zoom(factor=0.5)
    g.center_on(2)
    g._zoom(factor=0.5)
    g.center_on(2)
    start, end = g._view_start, g._view_end
    
    g._zoom(factor=0.5 * 0.5)
    g.center_on(2)
    assert (start, end) == (g._view_start, g._view_end)

def test_zoom_in():
    import numpy 
    from mock import Mock, Fake
    sound = Mock({"numchan": 1})
    sound.changed = Fake()

    data = numpy.array([1, 2, 3, 4])
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
    from mock import Mock, Fake
    sound = Mock({"numchan": 1})
    sound.changed = Fake()
    data = numpy.array([1, 2, 3, 4])
    sound.frames = data
    g = Graph(sound)
    g.set_width(2)

    g.zoom_in_on(0)
    assert g.channels() == [[(1, 1), (2, 2)]]

    g.zoom_out()
    g.zoom_in_on(1)
    assert g.channels() == [[(2, 2), (3, 3)]]

    g.zoom_out()
    g.zoom_in_on(2)
    assert g.channels() == [[(3, 3), (4, 4)]]

def test_scroll():
    import numpy
    from mock import Mock, Fake

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
    import edit
    g = Graph(edit.Sound("../sounds/test1.wav"))
    g.set_width(700)
    g.zoom_in()
    g.channels()
    g.zoom_in()
    g.channels()
    g.zoom_in()
    d = g.density()

    pos = [26744.9875, 18793.775, 15902.425, 13011.075, 10119.725, 7228.375,
           4337.025, 1445.675, 0.0, 2891.35, 5782.7, 8674.05, 11565.4,
           14456.75, 17348.1, 20239.45]

    for x in pos:
        g.move_to(x)
        assert d == g.density()

def test_channels():
    import numpy
    from mock import Mock, Fake
    sound = Mock({"numchan": 1})
    sound.changed = Fake()
    sound.frames = numpy.array(range(1000000))
    g = Graph(sound)

    for w in [1, 10, 11, 12, 13, 14, 15, 29, 54, 12.0, 347, 231., 1030]:
        g.set_width(w)
        c = g.channels()
        assert len(c[0]) == w, \
             "expected: %d, got: %d, density: %f, last value: %s " % \
                                     (w, len(c[0]), g.density(), str(c[0][-1]))

def test_OverviewCache():
    import numpy
    
    cache = OverviewCache()
    cache.set_data(numpy.array([1, 2, 3, 4]))
    o = cache.get(start=0, end=4, density=1)
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

    o2 = cache.get(start=0, end=4, density=1)
    assert o2 == o
    assert o2 is o

    cache.set_data(numpy.array([1, 2, 3, 4]))
    o3 = cache.get(start=0, end=4, density=1)
    assert o3 == o
    assert o3 is not o

if __name__ == "__main__":
    test_overview()
    test_Graph()
    test_middle()
    test_zoom()
    test_zoom_in()
    test_scroll()
    test_zoom_in_on()
    test_channels()
    test_OverviewCache()
    test_density()
