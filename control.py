from edit import Sound
from player import Player

class UIController(object):

    def __init__(self, sound, player, graph, selection):
        self._player = player
        self._graph = graph
        self._selection = selection
        self._sound = sound
        self.clipboard = []

    def new(self):
        pass

    def open(self, filename):
        self._player.pause()
        self._sound = Sound(filename)
        self._graph.set_sound(self._sound)
        self._player.set_sound(self._sound)
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
            end = len(self._sound._data)
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
        self._selection.start = start
        self._selection.end = start
        self.clip = self._sound.cut(start, end)
        
    def copy(self):
        start, end = self._selection.frames()
        self.clip = self._sound.copy(start, end)
        
    def paste(self):
        start, end = self._selection.frames()
        self._selection.start = start
        self._selection.end = start + len(self.clip)
        self._sound.paste(start, self.clip)

    def trim(self):
        pass

    def undo(self):
        self._sound.undo()

    def redo(self):
        self._sound.redo()

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

    def reverse(self):
        start, end = self._selection.frames()
        self._sound.reverse(start, end)

    def normalize(self):
        pass

    def scroll_right(self):
        pass

    def scroll_left(self):
        pass


def test_UIController():
    from time import sleep
    from mock import Fake
    
    # Test opening a file
    ctrl = UIController(Fake(), Fake(), Fake(), Fake())
    ctrl.open('sounds/test1.wav')
    assert ctrl._sound != None

if __name__ == "__main__":
    test_UIController()

