# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
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

    # frames is a numpy.ndarray, as returned by pysndfile
    
    def __init__(self, filename=None):
        self.filename = filename
        if filename == None:
            # empty sound
            self.frames = numpy.array([])
            self.numchan = 1
            self.samplerate = 44100
        else:
            f = pysndfile.sndfile(filename)
            nframes = f.get_nframes()
            self.frames = f.read_frames(nframes)
            self.numchan = f.get_channels()
            self.samplerate = f.get_samplerate()
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
        f.write_frames(self.frames)
        f.close()
        self.filename = filename

    def cut(self, start, end):
        clip = self.frames[start:end]
        do = (self._do_cut, (start, end))
        undo = (self._do_paste, (start, copy(self.frames[start:end])))
        self.history.add(do, undo)
        self.changed()
        return clip
    
    def _do_cut(self, start, end):
        data = numpy.concatenate((self.frames[:start], self.frames[end:]))
        self.frames = data

    def copy(self, start, end):
        clip = self.frames[start:end]
        return clip

    def paste(self, start, clip):
        do = (self._do_paste, (start, clip))
        undo = (self._do_cut, (start, start + len(clip)))
        self.history.add(do, undo)
        self.changed()

    def _do_paste(self, start, clip):
        data = numpy.concatenate((self.frames[:start], clip,self.frames[start:]))
        self.frames = data

    def apply(self, fx):
        self.history.add((fx.apply, ()), (fx.revert, ()))
        self.changed()

    def monoize(self, start, end):
        pass
    
    def undo(self):
        self.history.undo()
        self.changed()

    def redo(self):
        self.history.redo()
        self.changed()

    def is_fresh(self):
        """True if sound is empty and has never been edited."""
        return not len(self.frames) and not self.history._actions


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
    snd.frames = copy(sine)
    del sine2[start:end]
    snd.cut(start, end)
    assert snd.frames.tolist() == sine2

    snd.history.undo()
    assert snd.frames.tolist() == sine
    snd.history.undo()
    assert snd.frames.tolist() == sine
    snd.history.redo()
    assert snd.frames.tolist() == sine2

    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd.frames.tolist() == sine2[start:end] + sine2
    snd.history.undo()
    assert snd.frames.tolist() == sine2
    snd.history.redo()
    assert snd.frames.tolist() == sine2[start:end] + sine2
    
    # test with a mono file
    snd = Sound("../sounds/test1.wav")
    assert snd.frames != []
    start = 4444
    end = 55555
    data = snd.frames.tolist()
    data2 = snd.frames.tolist()
    del data2[start:end]
    snd.cut(start, end)
    assert snd.frames.tolist() == data2
    snd.history.undo()
    assert snd.frames.tolist() == data
    snd.history.undo()
    assert snd.frames.tolist() == data
    snd.history.redo()
    assert snd.frames.tolist() == data2
    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd.frames.tolist() == data2[start:end] + data2
    snd.history.undo()
    assert snd.frames.tolist() == data2
    snd.paste(0, clip)
    assert snd.frames.tolist() == data2[start:end] + data2

    # test with a stereo file
    snd = Sound("../sounds/test2.wav")
    assert snd.frames.tolist() != []
    start = 4444
    end = 55555
    data = copy(snd.frames.tolist())
    data2 = copy(snd.frames.tolist())
    del data2[start:end]
    snd.cut(start, end)
    assert snd.frames.tolist() == data2
    snd.history.undo()
    assert snd.frames.tolist() == data
    snd.history.undo()
    assert snd.frames.tolist() == data
    snd.history.redo()
    assert snd.frames.tolist() == data2
    clip = snd.copy(start, end)
    snd.paste(0, clip)
    assert snd.frames.tolist() == data2[start:end] + data2
    snd.history.undo()
    assert snd.frames.tolist() == data2
    snd.paste(0, clip)
    assert snd.frames.tolist() == data2[start:end] + data2

    # test save_as()
    import os
    snd = Sound("../sounds/test1.wav")
    outfile = "/tmp/test.wav"
    snd.save_as(outfile)
    assert os.path.exists(outfile)
    assert snd.filename == outfile
    snd2 = Sound(outfile)
    assert abs((snd.frames - snd2.frames).max()) < 0.0001 # quantization errors!
    os.remove(outfile)

    snd = Sound("../sounds/test2.wav")
    outfile = "/tmp/test2.wav"
    snd.save_as(outfile)
    assert os.path.exists(outfile)
    assert snd.filename == outfile
    snd2 = Sound(outfile)
    assert snd.frames.size == snd2.frames.size
    assert abs((snd.frames - snd2.frames).flatten().max()) == 0
    os.remove(outfile)

        
if __name__ == '__main__':
    testAction()
    testSound()
    testHistory()
