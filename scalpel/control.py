# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from edit import Sound
from player import Player
import app

class Clipboard(object):
    # OMG! A Borg! (http://code.activestate.com/recipes/66531/)
    __shared_state = {"clip": []}
    def __init__(self):
        self.__dict__ = self.__shared_state

class Controller(object):

    def __init__(self, sound, player, graph, selection):
        self._player = player
        self._graph = graph
        self._selection = selection
        self._sound = sound
        self.clipboard = Clipboard()

    def new(self):
        app.open_()

    def open(self, filename):
        if self._sound.is_fresh():
            self.load_sound(filename)
        else:
            app.open_(filename)

    def load_sound(self, filename):
        self._player.pause()
        self._sound = Sound(filename)
        self._graph.set_sound(self._sound)
        self._player.set_sound(self._sound)
        self._selection.unselect()

    def save(self):
        self._sound.save()

    def save_as(self, filename):
        self._sound.save_as(filename)

    def close(self):
        self._player.pause()

    def play(self):
        start, end = self._selection.get()
        if start == end:
            end = len(self._sound._data)
        self._player.start = start
        self._player.end = end
        self._player.thread_play()

    def pause(self):
        self._player.pause()

    def goto_start(self):
        self._selection.set(0, 0)

    def goto_end(self):
        end = len(self._sound._data)
        self._selection.set(end, end)

    def rewind(self):
        pass

    def forward(self):
        pass

    def cut(self):
        start, end = self._selection.get()
        self._selection.start = start
        self._selection.end = start
        self.clipboard.clip = self._sound.cut(start, end)
        
    def copy(self):
        start, end = self._selection.get()
        self.clipboard.clip = self._sound.copy(start, end)
        
    def paste(self):
        start, end = self._selection.get()
        # FIXME: error when number of channels doesn't match.
        self._sound.paste(start, self.clipboard.clip)
        self._selection.set(start, start + len(self.clipboard.clip))

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
        start, end = self._selection.get()
        self._sound.reverse(start, end)

    def normalize(self):
        pass

    def scroll_right(self):
        pass

    def scroll_left(self):
        pass


def test_Controller():
    from mock import Fake
    
    # Test opening a file
    ctrl = Controller(Fake(), Fake(), Fake(), Fake())
    ctrl.open('../sounds/test1.wav')
    assert ctrl._sound != None

if __name__ == "__main__":
    test_Controller()
