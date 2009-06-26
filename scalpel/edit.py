# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from event import Signal
from copy import copy
import pysndfile
import numpy

def list_extensions():
    extensions = pysndfile.supported_format()
    extensions.append('aif')
    return extensions


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
            self.samplerate = 44100
        else:
            f = pysndfile.sndfile(filename)
            nframes = f.get_nframes()
            self.frames = f.read_frames(nframes)
            self.samplerate = f.get_samplerate()
            f.close()
        self.history = History()
        self.changed = Signal()

    def numchan(self):
        return self.frames.ndim

    def save(self, format=pysndfile.formatinfo()):
        self.save_as(self.filename, format)

    def save_as(self, filename, format=pysndfile.formatinfo()):
        if filename is None:
            raise Exception("No filename")
        f = pysndfile.sndfile(filename, mode='write',
                              format=format,
                              channels=self.numchan(),
                              samplerate=44100)
        f.write_frames(self.frames)
        f.close()
        self.filename = filename

    def cut(self, start, end):
        clip = copy(self.frames[start:end])
        do = (self._do_cut, (start, end))
        undo = (self._do_paste, (start, start, copy(self.frames[start:end])))
        self.history.add(do, undo)
        self.changed()
        return clip
    
    def _do_cut(self, start, end):
        data = numpy.concatenate((self.frames[:start], self.frames[end:]))
        self.frames = data

    def copy(self, start, end):
        clip = copy(self.frames[start:end])
        return clip

    def paste(self, start, end, clip):
        saved = copy(self.frames[start:end])
        do = (self._do_paste, (start, end, clip))
        undo = (self._do_paste, (start, start + len(clip), saved))
        self.history.add(do, undo)
        self.changed()

    def _do_paste(self, start, end, clip):
        x = self.frames
        y = numpy.concatenate((x[:start], clip, x[end:]))
        self.frames = y

    def mix(self, start, end, clip):
        saved = copy(self.frames[start:start + len(clip)])
        do = (self._do_mix, (start, end, clip))
        undo = (self._do_paste, (start, start + len(clip), saved))
        self.history.add(do, undo)
        self.changed()

    def _do_mix(self, start, end, clip):
        if start != end:
            length = min(end - start, len(clip))
            self.frames[start:start + length] += clip[:length]
        else:
            a = self.frames
            b = clip
            sound_length = max(len(a), start + len(b))
            if self.numchan() > 1:
                c = numpy.zeros((sound_length, self.numchan()))
            else:
                c = numpy.zeros(sound_length)
            c[:len(a)] = a
            c[start:start + len(b)] += b
            self.frames = c

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
    snd.paste(0, 0, clip)
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
    snd.paste(0, 0, clip)
    assert snd.frames.tolist() == data2[start:end] + data2
    snd.history.undo()
    assert snd.frames.tolist() == data2
    snd.paste(0, 0, clip)
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
    snd.paste(0, 0, clip)
    assert snd.frames.tolist() == data2[start:end] + data2
    snd.history.undo()
    assert snd.frames.tolist() == data2
    snd.paste(0, 0, clip)
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

    # test cut
    snd = Sound()
    snd.frames = numpy.array([1, 2, 3, 4])
    clip = snd.cut(1, 3)
    assert snd.frames.tolist() == [1, 4]
    snd.undo()
    assert snd.frames.tolist() == [1, 2, 3, 4]
    # clip is a copy
    clip[0] = 9
    assert snd.frames.tolist() == [1, 2, 3, 4]

    # test copy
    snd = Sound()
    snd.frames = numpy.array([1, 2, 3, 4])
    clip = snd.copy(1, 3)
    assert clip.tolist() == [2, 3]
    # clip is a copy
    clip[0] = 9
    assert snd.frames.tolist() == [1, 2, 3, 4]

    # test paste
    snd = Sound()
    snd.frames = numpy.array([1, 2, 3, 4])
    clip = numpy.array([22, 33])
    snd.paste(1, 3, clip)
    assert snd.frames.tolist() == [1, 22, 33, 4]
    snd.undo()
    assert snd.frames.tolist() == [1, 2, 3, 4]
    snd.paste(1, 1, clip)
    assert snd.frames.tolist() == [1, 22, 33, 2, 3, 4]
    
    # test mix
    snd = Sound()
    snd.frames = numpy.array([1, 2, 3, 4])
    clip = numpy.array([2, 3])
    snd.mix(1, 3, clip)
    assert snd.frames.tolist() == [1, 4, 6, 4]
    snd.undo()
    assert snd.frames.tolist() == [1, 2, 3, 4]
    #
    # clip smaller than selection
    snd = Sound()
    snd.frames = numpy.array([1, 2, 3, 4])
    clip = numpy.array([2])
    snd.mix(1, 3, clip)
    assert snd.frames.tolist() == [1, 4, 3, 4]
    snd.undo()
    assert snd.frames.tolist() == [1, 2, 3, 4]
    #
    # must not go behind selection
    clip = numpy.array([2, 3, 4])
    snd.mix(1, 3, clip)
    assert snd.frames.tolist() == [1, 4, 6, 4]
    snd.undo()
    assert snd.frames.tolist() == [1, 2, 3, 4]

    clip = numpy.array([2, 3])
    snd.mix(1, 1, clip)
    assert snd.frames.tolist() == [1, 4, 6, 4]
    snd.undo()
    assert snd.frames.tolist() == [1, 2, 3, 4]
    #
    # mix() may extend sound length when there is no selection.
    clip = numpy.array([2, 3, 4, 5])
    snd.mix(1, 1, clip)
    assert snd.frames.tolist() == [1, 4, 6, 8, 5]
    snd.undo()
    assert snd.frames.tolist() == [1, 2, 3, 4]
    #
    # stereo too
    snd = Sound()
    snd.frames = numpy.array([[1, 1], [2, 2], [3, 3], [4, 4]])
    clip = numpy.array([[2, 2], [3, 3]])
    snd.mix(1, 3, clip)
    assert snd.frames.tolist() == [[1, 1], [4, 4], [6, 6], [4, 4]]
    snd.undo()
    assert snd.frames.tolist() == [[1, 1], [2, 2], [3, 3], [4, 4]]
    #
    snd = Sound()
    snd.frames = numpy.array([[1, 1], [2, 1], [3, 2], [4, 4]])
    clip = numpy.array([[2, 2], [3, 3]])
    snd.mix(1, 1, clip) # no selection
    assert snd.frames.tolist() == [[1, 1], [4, 3], [6, 5], [4, 4]]
    snd.undo()
    assert snd.frames.tolist() == [[1, 1], [2, 1], [3, 2], [4, 4]]

    # Do not crash when saving with None as filename
    snd = Sound()
    try:
        snd.save()
    except:
        print "OK"
    else:
        assert False
        
if __name__ == '__main__':
    testAction()
    testSound()
    testHistory()
