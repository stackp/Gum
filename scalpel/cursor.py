# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from event import Signal
from threading import Thread, Event, Lock

# Cursor position can be set by user interface. When Player is
# playing, Cursor regularly updates itself with its own thread.

class Repeat(Thread):
    """Regularly call a funtion.

    This object is a thread that calls a function repeatedly, with a
    delay between each call.

    """
    def __init__(self, function, delay):
        Thread.__init__(self)
        self._function = function
        self.delay = delay
        self.must_stop = Event()

    def run(self):
        while not self.must_stop.isSet():
            self._function()
            self.must_stop.wait(self.delay)

    def stop(self):
        """ Stop the thread. 

        Does not return until the thread is actually stopped.

        """
        self.must_stop.set()
        self.join()


class Cursor(object):
    """Cursor position (frame and pixel)."""
    def __init__(self, graph, player, selection):
        self._graph = graph
        self._player = player
        self._selection = selection
        self._frame = 0
        self._pixel = 0
        self.changed = Signal()
        self._follow = None
        self._player.start_playing.connect(self._on_start_playing)
        self._player.stop_playing.connect(self._on_stop_playing)
        self._graph.changed.connect(self._update_pixel)
        self._lock = Lock()

    def pixel(self):
        return self._pixel

    # set_frame() is called by two concurrent threads: Cursor._follow
    # and the main thread (through MouseSelection.button_release()).
    # A lock ensures atomicity.
    def set_frame(self, frame):
        self._lock.acquire()
        if frame != self._frame:
            self._frame = frame
            self._update_pixel()
        self._lock.release()

    def _update_pixel(self):
        pixel = self._graph.frmtopxl(self._frame)
        if pixel != self._pixel:
            self._pixel = pixel
            self.changed()

    def _on_start_playing(self):
        if not self._follow:
            self._follow = Repeat(self._store_player_position, 0.05)
            self._follow.start()

    def _on_stop_playing(self):
        if self._follow:
            self._follow.stop()
            self._follow = None
            frame, _ = self._selection.get()
            self.set_frame(frame)

    def _store_player_position(self):
        self.set_frame(self._player.position)
