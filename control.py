from edit import Sound
from player import Player

class UIController(object):

    def __init__(self, player, graph, selection):
        self._player = player
        self._graph = graph
        self._selection = selection
        self._sound = None

    def new(self):
        pass

    def open(self, filename):
        self._player.pause()
        self._sound = Sound(filename)
        self._graph.set_sound(self._sound)
        self._player.set_data(self._sound._data)
        self._selection.unselect()

    def save(self):
        pass

    def save_as(self, filename):
        pass

    def quit(self):
        pass

    def play(self):
        start, end = self._selection.frames()
        if start == end:
            end = len(self._player._data)
        self._position = start
        self._player.start = start
        self._player.end = end
        self._player.thread_play()

    def pause(self):
        self._player.pause()

    def goto_start(self):
        pass

    def goto_end(self):
        pass

    def rewind(self):
        pass

    def forward(self):
        pass

    def cut(self):
        start, end = self._selection.frames()
        self._sound.cut(start, end)
        self._selection.start = start
        self._selection.end = start
        
    def copy(self):
        pass

    def paste(self):
        pass

    def trim(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

    def select_all(self):
        pass

    def unselect(self):
        pass

    def zoom_out(self):
        self._graph.zoom_out()

    def zoom_in(self):
        self._graph.zoom_in()

    def zoom_fit(self):
        self._graph.zoom_fit()

    def scroll_right(self):
        pass

    def scroll_left(self):
        pass


def test_UIController():
    from time import sleep
    
    # Test opening a file
    ctrl = UIController()
    ctrl.open('sounds/test1.wav')
    assert ctrl._sound != None

    # Test playing
    assert ctrl._player != None
    ctrl.play()

    # Test pausing
    sleep(0.5)
    ctrl.pause()


if __name__ == "__main__":
    test_UIController()

