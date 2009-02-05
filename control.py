from edit import Sound
from player import Player

class UIController(object):

    def __init__(self, player, graphdata):
        self._player = player
        self._graphdata = graphdata
        self._snd = None

    def new(self):
        pass

    def open(self, filename):
        self._snd = Sound(filename)
        self._graphdata.set_data(self._snd._data)

    def save(self):
        pass

    def save_as(self, filename):
        pass

    def quit(self):
        pass

    def play(self, *args):
        self._player.thread_play(self._snd._data)

    def pause(self, *args):
        self._player.pause()
        pass

    def goto_start(self):
        pass

    def goto_end(self):
        pass

    def rewind(self):
        pass

    def forward(self):
        pass

    def cut(self):
        pass

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

    def zoom_out(self, *args):
        self._graphdata.zoom_out()

    def zoom_in(self, *args):
        self._graphdata.zoom_in()

    def zoom_fit(self, *args):
        self._graphdata.zoom_fit()

    def scroll_right(self):
        pass

    def scroll_left(self):
        pass


def test_UIController():
    from time import sleep
    
    # Test opening a file
    ctrl = UIController()
    ctrl.open('sounds/test1.wav')
    assert ctrl._snd != None

    # Test playing
    assert ctrl._player != None
    ctrl.play()

    # Test pausing
    sleep(0.5)
    ctrl.pause()


if __name__ == "__main__":
    test_UIController()

