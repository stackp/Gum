# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from event import Signal

def _overview(data, width):
    "Returns a list of (min, max) tuples."
    density = len(data) / float(width)
    if density < 1:
        density = 1
    left = 0
    end = len(data)
    res = []
    while round(left) < end:
        right = left + density
        if right > end:
            right = end
        i = int(round(left))
        j = int(round(right))
        d = data[i:j]
        mini = d.min()
        maxi = d.max()
        res.append((mini, maxi))
        left = right
    return res

class Graph(object):
    """Scale the sound visualization.
    
    When audio is drawn on the screen, several frames are condensed in
    one column of pixels. This object computes what to display,
    according to zooming and position in the sound.

    """
    def __init__(self, sound):
        self.changed = Signal()
        self._width = 100
        self.set_sound(sound)

    def set_sound(self, sound):
        self._sound = sound
        self._view_start = 0
        self._view_end = len(self._sound.frames)
        self._sound.changed.connect(self.update)
        self.changed()

    def update(self):
        "Called when sound has changed."
        self._adjust_view()
        self.changed()

    def move_to(self, value):
        "Moves the view start and keep the view length"
        l = self._view_end - self._view_start
        self._view_start = value
        self._view_end = value + l
        self.changed()

    def numframes(self):
        return len(self._sound.frames)
    
    def view(self):
        start = self._view_start
        end = self._view_end
        return (start, end)

    def density(self):
        "Number of frames per pixel."
        number_frames_view = (self._view_end - self._view_start)
        if number_frames_view < self._width:
            # sound is too small to fill the width
            d = 1
        else:
            d = float(number_frames_view) / self._width
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
        self._view_end = len(self._sound.frames)
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
        
    def channels(self):
        "Return the graph values."
        width = self._width
        numchan = self._sound.numchan
        start, end = [int(round(v)) for v in self._view_start, self._view_end]
        visible = self._sound.frames[start:end]
        if numchan == 1:
            o = [_overview(visible, width)]
        else:
            visible = visible.transpose()
            o = []
            for chan in range(numchan):
                values = _overview(visible[chan], width)
                o.append(values)
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
    print _overview(b, 30)
    
def test_Graph():
    from mock import Mock, Fake
    import numpy
    
    sound = Mock({})
    sound.frames = numpy.array(range(1000))
    sound.numchan = 1
    sound.changed = Fake()

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
    data = numpy.array([[1, 1], [2, 2], [3, 3]])
    sound.frames = data
    sound.numchan = 2
    o = c.channels()
    assert(len(o)) == 2
    

def test_zoom():
    from mock import Mock, Fake
    import numpy

    sound = Mock({})
    data = numpy.array([1, 2, 3, 4])
    sound.frames = data
    sound.numchan = 1
    sound.changed = Fake()

    g = Graph(sound)

    g.set_width(4)
    g._zoom(point=1.5, factor=1)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]
    
    g._zoom(point=0, factor=1)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

    g._zoom(point=6, factor=1)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]
    
    g.set_width(2)
    g._zoom(point=1.5, factor=0.5)
    o = g.channels()
    assert o == [[(2, 2), (3, 3)]]

    g._zoom(point=1.5, factor=0.5)
    g.set_width(4)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

    g.set_width(2)
    g._zoom(point=0, factor=0.5)
    o = g.channels()
    assert o == [[(1, 1), (2, 2)]]

    g.set_width(4)
    g._zoom(point=0, factor=0.25)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]
    
    g.set_width(4)
    g._zoom(point=4, factor=4)
    o = g.channels()
    assert o == [[(1, 1), (2, 2), (3, 3), (4, 4)]]

    g.set_width(3)
    data = numpy.array([1, 2, 3, 4, 5])
    sound.frames = data
    g._zoom(point=2, factor=0.5)
    o = g.channels()
    print o
    assert o == [[(2, 2), (3, 3), (4, 4)]]

    g._zoom(point=2, factor=0.5)
    g._zoom(point=2, factor=0.5)
    start, end = g._view_start, g._view_end
    
    g._zoom(point=2, factor=0.5 * 0.5)
    assert (start, end) == (g._view_start, g._view_end)

def test_zoom_in():
    import numpy 
    from mock import Mock, Fake
    sound = Mock({})
    sound.numchan = 1
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

def test_scroll():
    import numpy
    from mock import Mock, Fake

    sound = Mock({})
    data = numpy.array([1, 2, 3, 4])
    sound.frames = data
    sound.numchan = 1
    sound.changed = Fake()

    g = Graph(sound)
    g.set_width(4)

    g.scroll_right()
    length = g.numframes()
    start, end = g.view()
    assert length == 4
    assert start == 0
    assert end == 4

    
if __name__ == "__main__":
    test_overview()
    test_Graph()
    test_zoom()
    test_zoom_in()
    test_scroll()
