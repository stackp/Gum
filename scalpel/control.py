# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from edit import Sound
from player import Player
from event import Signal
import effect
import app
import traceback

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
        self.filename_changed = Signal()
        self.error = Signal()
        self.clipboard = Clipboard()

    def new(self):
        app.open_()

    def _report_exception(method):
        """Method decorator.

        Call the self.error signal when an exception was raised in the
        decorated method.

        """
        def wrapper(self, *args, **kwargs):
            try:
                method(self, *args, **kwargs)
            except Exception, e:
                print self.error("Error", str(e))
                traceback.print_exc()

        wrapper.__name__ = method.__name__
        wrapper.__doc__ = method.__doc__
        return wrapper

    @_report_exception
    def open(self, filename):
        if self._sound.is_fresh():
            self.load_sound(filename)
        else:
            app.open_(filename)

    @_report_exception
    def load_sound(self, filename):
        self._player.pause()
        self._sound = Sound(filename)
        self._graph.set_sound(self._sound)
        self._player.set_sound(self._sound)
        self._selection.unselect()
        self.filename_changed()

    @_report_exception
    def save(self):
        self._sound.save()

    @_report_exception
    def save_as(self, filename):
        self._sound.save_as(filename)
        self.filename_changed()

    def close(self):
        self._player.pause()

    def play(self):
        start, end = self._selection.get()
        if not self._selection.selected():
            end = len(self._sound.frames)
        self._player.start = start
        self._player.end = end
        self._player.thread_play()

    def pause(self):
        self._player.pause()

    def goto_start(self):
        self._selection.set(0, 0)

    def goto_end(self):
        end = len(self._sound.frames)
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
        
    @_report_exception
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
        self._selection.select_all()

    def zoom_out(self):
        self._graph.zoom_out()

    def zoom_in(self):
        self._graph.zoom_in()

    def zoom_fit(self):
        self._graph.zoom_fit()

    def reverse(self):
        self.effect('reverse')

    def normalize(self):
        self.effect('normalize')

    def effect(self, name):
        fx_class = effect.effects[name]
        if self._selection.selected():
            start, end = self._selection.get()
        else:
            start = 0
            end = len(self._sound.frames)
        fx = fx_class(self._sound, (start, end))
        self._sound.apply(fx)

    def scroll_right(self):
        pass

    def scroll_left(self):
        pass

    def filename(self):
        return self._sound.filename


def test_Controller():
    from mock import Fake
    
    # Test opening a file
    ctrl = Controller(Fake(), Fake(), Fake(), Fake())
    ctrl.open('../sounds/test1.wav')
    assert ctrl._sound != None

if __name__ == "__main__":
    test_Controller()
