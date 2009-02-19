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
        self._graph.changed.connect(self.update)
    
    def update(self):
        "Called when self._graph changes."
        self.density = self._graph.get_density()
        self.changed()

    def unselect(self):
        self.start = 0
        self.end = 0

    def start_selection(self, value):
        "The value is an index in the graph."
        length, view_start, view_end = self._graph.get_info()
        self.start = view_start + value * self.density
        self.end = self.start
        self.changed()
        
    def end_selection(self, value):
        "The value is an index in the graph."
        length, view_start, view_end = self._graph.get_info()
        self.end = view_start + value * self.density
        self.changed()

    def pixels(self):
        """Returns pixel position for selection: `(start, end)`.

        `start` is always lower than or equals to `end`.

        """
        (length, vstart, vend) = self._graph.get_info()
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
    graph = Mock({"get_density": 9, "get_info": (5000, 100.1, 200.1)})
    graph.changed = Fake()
    selection = Selection(graph)
    selection.start_selection(10)
    selection.end_selection(100)
    selection.update()
    assert selection.get_selection() == (10, 100)


if __name__ == "__main__":
    test_selection()
