# Gum sound editor (https://github.com/stackp/Gum)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from gum.lib.event import Signal

class Selection(object):
    """Represents a selection on a Graph object.

    Translates between frame numbers and pixels.

    """
    def __init__(self, graph, cursor):
        self._graph = graph
        self._cursor = cursor
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
        self._cursor.set_frame(min(self.start, self.end))
        self.changed()

    def unselect(self):
        self.set(0, 0)

    def select_all(self):
        self.set(0, self._graph.numframes())

    def select_till_start(self):
        start, end = self.get()
        self.set(0, end)

    def select_till_end(self):
        start, end = self.get()
        self.set(start, self._graph.numframes())

    def selected(self):
        return self.start != self.end

    def pin(self, pixel):
        "The pixel is an index in the graph."
        start = self._graph.pxltofrm(pixel)
        self.set(start, start)

    def extend(self, pixel):
        "The pixel is an index in the graph."
        self.end = self._graph.pxltofrm(pixel)
        self._cursor.set_frame(min(self.start, self.end))
        self.changed()

    def move_start_to_pixel(self, pixel):
        start, end = self.get()
        self.set(end, end)
        self.extend(pixel)

    def move_end_to_pixel(self, pixel):
        start, end = self.get()
        self.set(start, start)
        self.extend(pixel)

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
    from graph import Graph
    from gum.lib.mock import Fake

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

    x1, x2 = 10, 100
    selection = Selection(FakeGraph(), Fake())
    selection.pin(x1)
    selection.extend(x2)
    selection._update()
    assert selection.pixels() == (10, 100)
    assert selection.get() == (100 + 10 * x1, 100 + 10 * x2)

    # invert selection order
    selection.pin(x2)
    selection.extend(x1)
    selection._update()
    assert selection.pixels() == (10, 100)
    assert selection.get() == (100 + 10 * x1, 100 + 10 * x2)

    # select all
    selection.select_all()
    assert selection.get() == (0, 5000)
    assert selection.selected() == True

    # unselect
    selection.unselect()
    assert selection.selected() == False

if __name__ == "__main__":
    test_selection()
