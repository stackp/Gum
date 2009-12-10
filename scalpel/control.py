# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import edit
import clipboard
from player import Player
from event import Signal
import effect
import app
import traceback

class Controller(object):

    def __init__(self, sound, player, graph, selection):
        self._player = player
        self._graph = graph
        self._selection = selection
        self._sound = sound
        self.filename_changed = Signal()
        self.error = Signal()
        self.clipboard = clipboard.Clipboard()

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
                self.error("Error", str(e))
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
        self._player.stop()
        self._sound = edit.Sound(filename)
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

    @_report_exception
    def save_selection_as(self, filename):
        sound = edit.Sound()
        if not self._selection.selected():
            raise Exception("There is no selection.")
        start, end = self._selection.get()
        sound.frames = self._sound.copy(start, end)
        sound.samplerate = self._sound.samplerate
        sound.save_as(filename)

    def close(self, force=False):
        sound = self._sound
        if not sound.is_saved() and not sound.is_fresh() and not force:
            raise FileNotSaved
        self._player.stop()

    def play(self):
        start, end = self._selection.get()
        if not self._selection.selected():
            end = len(self._sound.frames)
        self._player.start = start
        self._player.end = end
        self._player.thread_play()

    def stop(self):
        self._player.stop()

    def toggle_play(self):
        if self._player._playing:
            self.stop()
        else:
            self.play()

    def goto_start(self):
        self._selection.set(0, 0)
        self._graph.move_to(0)

    def goto_end(self):
        end = len(self._sound.frames)
        self._selection.set(end, end)

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
        was_zoomed_out_full = self._graph.is_zoomed_out_full()
        self._sound.paste(start, end, self.clipboard.clip)
        self._selection.set(start, start + len(self.clipboard.clip))
        if was_zoomed_out_full:
            self._graph.zoom_out_full()

    @_report_exception
    def mix(self):
        start, end = self._selection.get()
        self._sound.mix(start, end, self.clipboard.clip)
        # FIXME: should be dealt with in Sound.
        if start == end:
            l = len(self.clipboard.clip)
        else:
            l = min(end - start, len(self.clipboard.clip))
        self._selection.set(start, start + l)

    def trim(self):
        pass

    def undo(self):
        self._sound.undo()
        self.fix_selection()

    def redo(self):
        self._sound.redo()
        self.fix_selection()

    def fix_selection(self):
        start, end = self._selection.get()
        n = len(self._sound.frames)
        if end > n:
            # Selection has become invalid.
            start = min(start, n)
            end = n
            self._selection.set(start, end)

    def select_all(self):
        self._selection.select_all()

    def zoom_out(self):
        self._graph.zoom_out()

    def zoom_in(self):
        self._graph.zoom_in()

    def zoom_fit(self):
        if self._selection.selected():
            start, end = self._selection.get()
            self._graph.set_view(start, end)
        else:
            self._graph.zoom_out_full()

    def effect(self, name):
        if self._selection.selected():
            start, end = self._selection.get()
        else:
            start = 0
            end = len(self._sound.frames)
        fx = effect.effects[name]
        fx(self._sound, start, end)

    def filename(self):
        return self._sound.filename

class FileNotSaved: pass

def test_Controller():
    from mock import Fake
    
    # Test opening a file
    ctrl = Controller(Fake(), Fake(), Fake(), Fake())
    ctrl.open('../sounds/test1.wav')
    assert ctrl._sound != None

def test_fix_selection():
    from mock import Fake, Mock
    from selection import Selection
    import numpy

    # Undo
    graph = Mock({})
    graph.changed = Fake()
    selection = Selection(graph, Fake())
    sound = edit.Sound()
    sound.frames = numpy.array(range(1000))
    ctrl = Controller(sound, Fake(), Fake(), selection)
    frames = sound.frames
    selection.set(0, 999)
    ctrl.copy()
    ctrl.paste()
    selection.set(1500, 1500)
    ctrl.undo()
    ctrl.paste()
    ctrl.undo()
    assert sound.frames.tolist() == frames.tolist()

    # Redo
    graph = Mock({})
    graph.changed = Fake()
    selection = Selection(graph, Fake())
    sound = edit.Sound()
    sound.frames = numpy.array(range(1000))
    ctrl = Controller(sound, Fake(), Fake(), selection)
    frames = sound.frames
    selection.set(10, 999)
    ctrl.cut()
    ctrl.undo()
    selection.set(900, 900)
    ctrl.redo()
    frames = sound.frames 
    ctrl.paste()
    ctrl.undo()
    assert sound.frames.tolist() == frames.tolist()
    

if __name__ == "__main__":
    test_Controller()
    test_fix_selection()
