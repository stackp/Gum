# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from event import Signal
from copy import copy
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

    def _push(self, action):
        if self._last < len(self._actions) - 1:
            # erase previously undone actions
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

    def add(self, do, undo):
        "Does an action and adds it to history."
        action = Action(do, undo)
        self._push(action)
        return action.do()

class Sound(object):

    # _data is a numpy.ndarray, as returned by pysndfile
    
    def __init__(self, filename=None):
        self.filename = filename
        if filename == None:
            # empty sound
            self._data = numpy.array([])
            self.numchan = 1
        else:
            f = pysndfile.sndfile(filename)
            nframes = f.get_nframes()
            self._data = f.read_frames(nframes)
            self.numchan = f.get_channels()
            f.close()
        self.history = History()
        self.changed = Signal()

    def save(self, format=pysndfile.formatinfo()):
        self.save_as(self.filename, format)

    def save_as(self, filename, format=pysndfile.formatinfo()):
        f = pysndfile.sndfile(filename, mode='write',
                              format=format,
                              channels=self.numchan,
                              samplerate=44100)
        f.write_frames(self._data)
        f.close()
        self.filename = filename

    def cut(self, start, end):
        clip = self._data[start:end]
        do = (self._do_cut, (start, end))
        undo = (self._do_paste, (start, self._data[start:end]))
        self.history.add(do, undo)
        return clip
    
    def _do_cut(self, start, end):
        data = numpy.concatenate((self._data[:start], self._data[end:]))
        self._data = data
        self.changed()

    def copy(self, start, end):
        clip = self._data[start:end]
        return clip

    def paste(self, start, clip):
        do = (self._do_paste, (start, clip))
        undo = (self._do_cut, (start, start + len(clip)))
        self.history.add(do, undo)

    def _do_paste(self, start, clip):
        data = numpy.concatenate((self._data[:start], clip,self._data[start:]))
        self._data = data
        self.changed()
        
    def normalize(self, start, end):
        pass

    def reverse(self, start, end):
        do = (self._do_reverse, (start, end))
        undo = (self._do_reverse, (start, end))
        self.history.add(do, undo)

    def _do_reverse(self, start, end):
        rev = numpy.flipud(copy(self._data[start:end]))
        self._data[start:end] = rev
        self.changed()

    def monoize(self, start, end):
        pass
    
    def undo(self):
        self.history.undo()

    def redo(self):
        self.history.redo()


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
    assert history.add(do, undo) == 1
    assert history.undo() == 2
    assert history.undo() == None
    assert history.redo() == 1
    assert history.redo() == None
    assert history.undo() == 2
    assert history.add(do, undo) ==  1
    assert history.add(do, undo) == 1
    assert history.undo() == 2
    assert history.undo() == 2
    assert history.redo() == 1
    assert history.redo() == 1
    assert history.redo() == None
    
def testSound():
    from copy import copy
    snd = Sound()

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
    assert snd._data.tolist() == sine2

    snd.history.undo()
    assert snd._data.tolist() == sine
    snd.history.undo()
    assert snd._data.tolist() == sine
    snd.history.redo()
    assert snd._data.tolist() == sine2

    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd._data.tolist() == sine2[start:end] + sine2
    snd.history.undo()
    assert snd._data.tolist() == sine2
    snd.history.redo()
    assert snd._data.tolist() == sine2[start:end] + sine2
    
    # test with a mono file
    snd = Sound("../sounds/test1.wav")
    assert snd._data != []
    start = 4444
    end = 55555
    data = snd._data.tolist()
    data2 = snd._data.tolist()
    del data2[start:end]
    snd.cut(start, end)
    assert snd._data.tolist() == data2
    snd.history.undo()
    assert snd._data.tolist() == data
    snd.history.undo()
    assert snd._data.tolist() == data
    snd.history.redo()
    assert snd._data.tolist() == data2
    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd._data.tolist() == data2[start:end] + data2
    snd.history.undo()
    assert snd._data.tolist() == data2
    snd.paste(0, clip)
    assert snd._data.tolist() == data2[start:end] + data2

    # test with a stereo file
    snd = Sound("../sounds/test2.wav")
    assert snd._data.tolist() != []
    start = 4444
    end = 55555
    data = copy(snd._data.tolist())
    data2 = copy(snd._data.tolist())
    del data2[start:end]
    snd.cut(start, end)
    assert snd._data.tolist() == data2
    snd.history.undo()
    assert snd._data.tolist() == data
    snd.history.undo()
    assert snd._data.tolist() == data
    snd.history.redo()
    assert snd._data.tolist() == data2
    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd._data.tolist() == data2[start:end] + data2
    snd.history.undo()
    assert snd._data.tolist() == data2
    snd.paste(0, clip)
    assert snd._data.tolist() == data2[start:end] + data2

    # test reverse()
    snd = Sound()
    snd._data = numpy.array(range(10))
    snd.reverse(3, 6)
    assert snd._data.tolist() == [0, 1, 2, 5, 4, 3, 6, 7, 8, 9]

    snd._data = numpy.array(zip(range(8), range(8)))
    snd.reverse(3, 6)
    assert snd._data.tolist() == [[0, 0], [1, 1], [2, 2], [5, 5],
                                  [4, 4], [3, 3], [6, 6], [7, 7]]

    # test save_as()
    import os
    snd = Sound("../sounds/test1.wav")
    outfile = "/tmp/test.wav"
    snd.save_as(outfile)
    assert os.path.exists(outfile)
    assert snd.filename == outfile
    snd2 = Sound(outfile)
    assert abs((snd._data - snd2._data).max()) < 0.0001 # quantization errors!
    os.remove(outfile)

    snd = Sound("../sounds/test2.wav")
    outfile = "/tmp/test2.wav"
    snd.save_as(outfile)
    assert os.path.exists(outfile)
    assert snd.filename == outfile
    snd2 = Sound(outfile)
    assert snd._data.size == snd2._data.size
    assert abs((snd._data - snd2._data).flatten().max()) == 0
    os.remove(outfile)

        
if __name__ == '__main__':
    testAction()
    testSound()
    testHistory()
