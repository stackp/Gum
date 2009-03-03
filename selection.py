from event import Signal

class Selection(object):
    """Represents a selection on a Graph object.

    Translates between frame numbers and pixels.

    """
    def __init__(self, graph):
        self._graph = graph
        self.changed = Signal()
        self.density = self._graph.get_density()
        self.unselect()
        self._graph.changed.connect(self._update)
    
    def _update(self):
        "Called when self._graph changes."
        self.density = self._graph.get_density()
        self.changed()

    def set(self, start, end):
        "Set selection bounds (in frames)"
        self.start = start
        self.end = end
        self.changed()

    def unselect(self):
        self.start = 0
        self.end = 0

    def gauge(self, value, mini, maxi):
        "Calibrate value between mini and maxi."
        if value < mini:
            value = mini
        if value > maxi:
            value = maxi
        return value
    
    def start_selection(self, pixel):
        "The pixel is an index in the graph."
        length, view_start, view_end = self._graph.frames_info()
        start = view_start + pixel * self.density
        self.start = self.gauge(start, 0, length)
        self.end = self.start
        self.changed()
        
    def end_selection(self, pixel):
        "The pixel is an index in the graph."
        length, view_start, view_end = self._graph.frames_info()
        end = view_start + pixel * self.density
        self.end = self.gauge(end, 0, length)
        self.changed()

    def pixels(self):
        """Returns pixel position for selection: `(start, end)`.

        `start` is always lower than or equals to `end`.

        """
        (length, vstart, vend) = self._graph.frames_info()
        pix_start = int(round((self.start - vstart) / self.density))
        pix_end = int(round((self.end - vstart) / self.density))
        if pix_start > pix_end:
            pix_start, pix_end = pix_end, pix_start
        return pix_start, pix_end

    def frames(self):
        """Returns frames index for selection: (start, end).

        start is always lower than or equals to end.

        """
        start = int(round(self.start))
        end = int(round(self.end))
        if start > end:
            start, end = end, start
        return start, end
    
def test_selection():
    from mock import Fake, Mock
    graph = Mock({"get_density": 10, "frames_info": (5000, 100.1, 200.1)})
    graph.changed = Fake()
    selection = Selection(graph)
    selection.start_selection(10)
    selection.end_selection(100)
    selection._update()
    assert selection.pixels() == (10, 100)
    assert selection.frames() == (100 + 10 *  10, 100 + 10 * 100)

if __name__ == "__main__":
    test_selection()
