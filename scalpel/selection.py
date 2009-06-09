# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from event import Signal

class Selection(object):
    """Represents a selection on a Graph object.

    Translates between frame numbers and pixels.

    """
    def __init__(self, graph):
        self._graph = graph
        self.changed = Signal()
        self.unselect()
        self._graph.changed.connect(self._update)
    
    def _update(self):
        "Called when self._graph changes."
        self.changed()

    def set(self, start, end):
        "Set selection bounds (in frames)"
        self.start = start
        self.end = end
        self.changed()

    def unselect(self):
        self.start = 0
        self.end = 0
    
    def start_selection(self, pixel):
        "The pixel is an index in the graph."
        self.start = self._graph.pxltofrm(pixel)
        self.end = self.start
        self.changed()
        
    def end_selection(self, pixel):
        "The pixel is an index in the graph."
        self.end = self._graph.pxltofrm(pixel)
        self.changed()

    def pixels(self):
        """Returns pixel position for selection: `(start, end)`.

        `start` is always lower than or equals to `end`.

        """
        frame_start, frame_end = self.get()
        pix_start = self._graph.frmtopxl(frame_start)
        pix_end = self._graph.frmtopxl(frame_end)
        return pix_start, pix_end

    def get(self):
        """Returns frames index for selection: (start, end).

        start is always lower than or equal to end.

        """
        start = self.start
        end = self.end
        if start > end:
            start, end = end, start
        return start, end

    
def test_selection():
    from graphmodel import Graph
    from mock import Fake

    class FakeGraph():
        density = 10
        numframes = (lambda(self): 5000)
        _view_start = 100.1
        _view_end = 200.1
        changed = Fake()

        def frmtopxl(self, f):
            return int(round(f - self._view_start) / self.density)

        def pxltofrm(self, p):
            return int(round(self._view_start + p * self.density))

    selection = Selection(FakeGraph())
    x1, x2 = 10, 100
    selection.start_selection(x1)
    selection.end_selection(x2)
    selection._update()
    assert selection.pixels() == (10, 100)
    assert selection.get() == (100 + 10 * x1, 100 + 10 * x2)

    # invert selection order
    selection.start_selection(x2)
    selection.end_selection(x1)
    selection._update()
    assert selection.pixels() == (10, 100)
    assert selection.get() == (100 + 10 * x1, 100 + 10 * x2)

if __name__ == "__main__":
    test_selection()
