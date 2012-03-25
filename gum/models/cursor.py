# Gum sound editor (https://github.com/stackp/Gum)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from gum.lib.event import Signal
from threading import Thread, Event, Lock

# Cursor position can be set by a Selection object. When Player is
# playing, Cursor regularly updates itself with its own thread.

class Repeat(Thread):
    """Regularly call a function.

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
    """Cursor position (frame and pixel).

    When the player is playing, pixel() returns the player position,
    otherwise the position that was set (through a Selection object)
    is returned.

    """
    def __init__(self, graph, player):
        self._graph = graph
        self._player = player
        # Position set through a Selection object
        self._frame = 0
        # Position of the player
        self._player_frame = 0
        self._pixel = 0
        self.changed = Signal()
        self._player.start_playing.connect(self._on_start_playing)
        self._player.stop_playing.connect(self._on_stop_playing)
        self._graph.changed.connect(self._on_graph_changed)
        self._follow = None
        self._lock = Lock()

    def pixel(self):
        return self._pixel

    def set_frame(self, frame):
        """This method may be called by a Selection object."""
        self._frame = frame
        if not self._follow:
            self._update_pixel(frame)

    def _set_player_frame(self, frame):
        """This method is only called by self._follow thread."""
        self._player_frame = frame
        self._update_pixel(frame)

    # This method may be called concurrently. A lock ensures
    # atomicity.
    def _update_pixel(self, frame):
        self._lock.acquire()
        pixel = self._graph.frmtopxl(frame)
        if pixel != self._pixel:
            self._pixel = pixel
            self.changed()
        self._lock.release()

    def _on_graph_changed(self):
        if self._follow:
            self._update_pixel(self._player_frame)
        else:
            self._update_pixel(self._frame)

    def _on_start_playing(self):
        if not self._follow:
            self._follow = Repeat(self._store_player_position, 0.05)
            self._follow.start()

    def _on_stop_playing(self):
        if self._follow:
            self._follow.stop()
            self._follow = None
        self.set_frame(self._frame)

    def _store_player_position(self):
        self._set_player_frame(self._player.position)


if __name__ == "__main__":

    def test():
        import time
        from gum.lib.mock import Fake

        class Empty: pass

        graph = Empty()
        graph.changed = Fake()
        graph.frmtopxl = lambda x: x
        player = Empty()
        player.start_playing = Fake()
        player.stop_playing = Fake()
        c = Cursor(graph, player)

        c.set_frame(5)
        assert c.pixel() == 5

        player.position = 0
        c._on_start_playing()
        time.sleep(0.2)
        assert c.pixel() == 0
        c.set_frame(10)
        assert c.pixel() == 0
        c._on_stop_playing()
        time.sleep(0.2)
        assert c.pixel() == 10

    test()
