from event import Signal
import pysndfile
import numpy

class Action(object):
    """Describes an action, and a way to revert that action"""
     
    def __init__(self, do, undo):
        """do and undo are tuples in the form (fun, args) where fun is a
        function and args contains the arguments"""
        self._do = do
        self._undo = undo

    def do(self):
        fun, args = self._do
        return fun(*args)

    def undo(self):
        fun, args = self._undo
        return fun(*args)


class History(object):
    "A list of actions, that can be undone and redone."

    def __init__(self):
        self._actions = []
        self._last = -1

    def push(self, action):
        if self._last < len(self._actions) - 1:
            del self._actions[self._last + 1:]
        self._actions.append(action)
        self._last = self._last + 1
        
    def undo(self):
        if self._last < 0:
            return None
        else:
            action = self._actions[self._last]
            self._last = self._last - 1
            return action.undo()
            
    def redo(self):
        if self._last == len(self._actions) - 1:
            return None
        else:
            self._last = self._last + 1
            action = self._actions[self._last]
            return action.do()


class Sound(object):

    # _data is a numpy.ndarray, as returned by pysndfile

    # For convenience, some operations (ex: cut(), copy(), ...) are
    # performed on list(_data), and the result is then converted to a
    # numpy array.
    
    def __init__(self, filename=None):
        self.filename = filename
        if filename == None:
            # empty sound
            self._data = []
        else:
            f = pysndfile.sndfile(filename)
            nframes = f.get_nframes()
            self._data = f.read_frames(nframes)
        self.history = History()
        self.changed = Signal()

    def save(self, format):
        self.save_as(self.filename, format)

    def save_as(self, filename, format):
        pass

    def cut(self, start, end):
        clip = self._data[start:end]
        do = (self._do_cut, (start, end))
        undo = (self._do_paste, (start, self._data[start:end]))
        action = Action(do, undo)
        action.do()
        self.history.push(action)
        self.changed()
        return clip
    
    def _do_cut(self, start, end):
        # using del on numpy.ndarray raises a ValueError. Converting
        # to list.
        data = list(self._data)
        del data[start:end]
        self._data = numpy.array(data)

    def copy(self, start, end):
        clip = self._data[start:end]
        return clip

    def paste(self, start, clip):
        do = (self._do_paste, (start, clip))
        undo = (self._do_cut, (start, start + len(clip)))
        action = Action(do, undo)
        action.do()
        self.history.push(action)
        self.changed()

    def _do_paste(self, start, clip):
        data = list(self._data)
        data = data[:start] + list(clip) + data[start:]
        self._data = numpy.array(data)
        
    def normalize(self, start, end):
        pass

    def reverse(self, start, end):
        pass

    def monoize(self, start, end):
        pass
    
    def undo(self):
        self.history.undo()
        self.changed()

    def redo(self):
        self.history.redo()
        self.changed()


# -- Tests

def testAction():
    f = lambda x: x
    do = (f, (1,))
    undo = (f, (2,))
    a = Action(do, undo)
    assert a.do() == 1
    assert a.undo() == 2

    g = lambda : 1
    do = (g, ())
    undo = (g, ())
    a = Action(do, undo)
    assert a.do() == 1
    assert a.undo() == 1


def testHistory():
    history = History()
    f = lambda x: x
    do = (f, (1,))
    undo = (f, (2,))    
    action = Action(do, undo)
    history.push(action)
    assert history.undo() == 2
    assert history.undo() == None
    assert history.redo() == 1
    assert history.redo() == None
    assert history.undo() == 2
    history.push(action)
    history.push(action)
    assert history.undo() == 2
    assert history.undo() == 2
    assert history.redo() == 1
    assert history.redo() == 1
    assert history.redo() == None
    
    
def testSound():
    from copy import copy
    snd = Sound()
    assert snd._data == []

    # synthesize a sine wave
    from math import sin
    SR = 44100
    f0 = 440
    time = 5
    sine = [sin(2 * 3.14 * f0/SR * x) for x in range(time * SR)]
    start, end = 2*SR, 4*SR
    sine2 = copy(sine)
    snd._data = copy(sine)
    del sine2[start:end]
    snd.cut(start, end)
    assert snd._data == sine2

    snd.history.undo()
    assert snd._data == sine
    snd.history.undo()
    assert snd._data == sine
    snd.history.redo()
    assert snd._data == sine2

    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd._data == sine2[start:end] + sine2
    snd.history.undo()
    assert snd._data == sine2
    snd.history.redo()
    assert snd._data == sine2[start:end] + sine2
    
    # test with a mono file
    snd = Sound("sounds/test1.wav")
    assert snd._data != []
    start = 4444
    end = 55555
    data = copy(snd._data)
    data2 = copy(snd._data)
    del data2[start:end]
    snd.cut(start, end)
    assert snd._data == data2
    snd.history.undo()
    assert snd._data == data
    snd.history.undo()
    assert snd._data == data
    snd.history.redo()
    assert snd._data == data2
    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd._data == data2[start:end] + data2
    snd.history.undo()
    assert snd._data == data2
    snd.paste(0, clip)
    assert snd._data == data2[start:end] + data2

    # test with a stereo file
    snd = Sound("sounds/test2.wav")
    assert snd._data != []
    start = 4444
    end = 55555
    data = copy(snd._data)
    data2 = copy(snd._data)
    del data2[start:end]
    snd.cut(start, end)
    assert snd._data == data2
    snd.history.undo()
    assert snd._data == data
    snd.history.undo()
    assert snd._data == data
    snd.history.redo()
    assert snd._data == data2
    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd._data == data2[start:end] + data2
    snd.history.undo()
    assert snd._data == data2
    snd.paste(0, clip)
    assert snd._data == data2[start:end] + data2

if __name__ == '__main__':
    testAction()
    testSound()
    testHistory()
