# Gum sound editor (https://github.com/stackp/Gum)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from gum.lib.event import Signal
from gum.lib import pysndfile, history
from scikits import samplerate
from copy import copy
import os.path
import numpy

def list_extensions():
    extensions = pysndfile.supported_format()
    extensions.append('aif')
    return extensions


class Sound(object):

    # frames is a numpy.ndarray, as returned by pysndfile
    
    def __init__(self, filename=None):
        self.filename = filename
        self.history = history.History()
        self.changed = Signal()
        if filename == None:
            # empty sound
            self.frames = numpy.array([])
            self.samplerate = 44100
            self._saved_revision = None
            self._format = pysndfile.formatinfo()
        else:
            filename = os.path.expanduser(filename)
            f = pysndfile.sndfile(filename)
            nframes = f.get_nframes()
            self.frames = f.read_frames(nframes)
            self.samplerate = f.get_samplerate()
            self._format = f._format
            f.close()
            self._saved_revision = self.history.revision()

    def numchan(self):
        return self.frames.ndim

    def save(self):
        self.save_as(self.filename)

    def save_as(self, filename):
        if filename is None:
            raise Exception("No filename")
        f = pysndfile.sndfile(filename, mode='write',
                              format=self._format,
                              channels=self.numchan(),
                              samplerate=self.samplerate)
        f.write_frames(self.frames)
        f.close()
        self.filename = filename
        self._saved_revision = self.history.revision()

    def cut(self, start, end):
        clip = copy(self.frames[start:end])
        do = (self._do_cut, (start, end))
        undo = (self._do_paste, (start, start, clip))
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
        if self.is_empty():
            self.frames = clip
        else:
            # FIXME: should resample
            clip = mix_channels_auto(clip, self.numchan())
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
        if self.is_empty():
            self.frames = clip
        else:
            # FIXME: should resample
            clip = mix_channels_auto(clip, self.numchan())
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

    def undo(self):
        self.history.undo()
        self.changed()

    def redo(self):
        self.history.redo()
        self.changed()

    def is_empty(self):
        return not len(self.frames)

    def is_fresh(self):
        """True if sound is empty and has never been edited."""
        return self.is_empty() and self.history.is_empty()

    def is_saved(self):
        return self._saved_revision == self.history.revision()


def resample(frames, ratio):
    new = samplerate.resample(frames, ratio, 'sinc_best')
    return numpy.array(new, dtype='float64')


def mix_channels(frames, gain_lists):
    """Mix channels into a possibly different number of channels.

    * len(gain_lists) defines the number of output channels,
    * gain_lists[n] contains gains to mix input channels into output
      channel number n. Consequently, len(gain_lists[n]) == frames.ndim.
    
    Returns the mixed signal.

    Examples::

          # mono to stereo
          mix_channels(frames, [[1], [1]])

          # stereo to mono
          mix_channels(frames, [[0.5, 0.5]])

    """
    numchan = frames.ndim
    assert len(gain_lists[0]) == numchan

    # special case for monophonic sounds
    if numchan == 1:
        channels = [frames]
    else:
        channels = frames.transpose()

    # apply gains
    out = []
    for gain_list in gain_lists:
        new_channel = numpy.zeros(len(frames))
        for g, channel in zip(gain_list, channels):
            new_channel += g * channel
        out.append(new_channel)

    # special case for monophonic sounds
    if len(out) == 1:
        out = out[0]
        out = numpy.array(out)
    else:
        out = numpy.array(out)
        out = out.transpose()

    return out

def mix_channels_auto(frames, n):
    """Convert the number of channels.

    Used in Sound.paste() and Sound.mix() to convert the clipboard to
    the right number of channels.
    
    This should probably be a Sound method and the clipboard should
    contain a Sound instance instead of just a numpy array.

    Examples::

          # to stereo
          mix_channels_auto(frames, 2)

          # to mono
          mix_channels(frames, 1)

    """
    numchan = frames.ndim
    if n == numchan:
        out = frames
    else:
        if n == 1:
            # monoize
            g = 1. / numchan
            gain_list = [g] * numchan
            gain_lists = [gain_list]
        elif numchan == 1:
            # mono to n channels
            gain_lists = [[1]] * n
        else:
            raise Exception("Don't know yet how to deal with so many channels")
        out = mix_channels(frames, gain_lists)

    return out

# -- Tests

def testSound():
    from copy import copy
    import gum
    testdir = gum.basedir + '/data/test'
    snd = Sound()

    # synthesize a sine wave
    from math import sin
    SR = 44100
    f0 = 440
    time = 5
    sine = [sin(2 * 3.14 * f0/SR * x) for x in range(time * SR)]
    start, end = 2*SR, 4*SR
    sine2 = copy(sine)
    snd.frames = numpy.array(copy(sine))
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
    snd = Sound(testdir + "/test1.wav")
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
    snd = Sound(testdir + "/test2.wav")
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
    snd = Sound(testdir + "/test1.wav")
    outfile = "/tmp/test.wav"
    snd.save_as(outfile)
    assert os.path.exists(outfile)
    assert snd.filename == outfile
    snd2 = Sound(outfile)
    assert abs((snd.frames - snd2.frames).max()) < 0.0001 # quantization errors!
    os.remove(outfile)

    snd = Sound(testdir + "/test2.wav")
    outfile = "/tmp/test2.wav"
    snd.save_as(outfile)
    assert os.path.exists(outfile)
    assert snd.filename == outfile
    snd2 = Sound(outfile)
    assert snd.frames.size == snd2.frames.size
    assert abs((snd.frames - snd2.frames).flatten().max()) == 0
    os.remove(outfile)

    # Preserve file format when saving
    snd = Sound(testdir + "/test3.wav")
    outfile = "/tmp/test3.wav"
    snd.save_as(outfile)
    snd2 = Sound(outfile)
    assert snd2._format.type == 'wavex'
    assert snd2._format.encoding == 'pcm24'
    assert snd2._format.endianness == 'file'
    assert snd.samplerate == 48000
    os.remove(outfile)
    

    # test mix_channels
    #
    # stereo to mono
    frames = numpy.array([[1, 1], [2, 2], [3, 3], [4, 4]])
    out = mix_channels(frames, [[0.5, 0.5]])
    assert out.tolist() == [1, 2, 3, 4]
    #
    # mono to stereo
    frames = numpy.array([1, 2, 3, 4])
    out = mix_channels(frames, [[1], [1]])
    assert out.tolist() == [[1, 1], [2, 2], [3, 3], [4, 4]]
    #
    # channel 0 to stereo
    c0 = [1, 2, 3, 4]
    c1 = [5, 6, 7, 8]
    frames = numpy.array([c0, c1]).transpose()
    out = mix_channels(frames, [[1, 0], [1, 0]])
    assert out.tolist() == [[1, 1], [2, 2], [3, 3], [4, 4]]

    # test mix_channels_auto()
    #
    # stereo to mono
    snd = Sound()
    frames = numpy.array([[1, 1.5], [2, 2.5], [3, 3.5], [4, 4.5]])
    out = mix_channels_auto(frames, 1)
    assert out.tolist() == [1.25, 2.25, 3.25, 4.25]
    #    
    # mono to stereo
    frames = numpy.array([1, 2, 3, 4])
    out = mix_channels_auto(frames, 2)
    assert out.tolist() == [[1, 1], [2, 2], [3, 3], [4, 4]]
    #
    # 1 --> 3
    frames = numpy.array([1, 2, 3, 4])
    out = mix_channels_auto(frames, 3)
    assert out.tolist() == [[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]]
    # 
    # no change
    frames = numpy.array([1, 2, 3, 4])
    out = mix_channels_auto(frames, 1)
    assert out.tolist() == [1, 2, 3, 4]

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
    #
    # paste a stereo clip into a mono file
    snd.frames = numpy.array([1, 2, 3, 4])
    clip = numpy.array([[30, 10], [40, 20]])
    snd.paste(1, 3, clip)
    assert snd.frames.tolist() == [1, 20, 30, 4]
    snd.undo()
    assert snd.frames.tolist() == [1, 2, 3, 4]
    snd.paste(1, 1, clip)
    assert snd.frames.tolist() == [1, 20, 30, 2, 3, 4]
    # pasting in empty sound: keep it stereo
    snd.frames = numpy.array([])
    snd.paste(1, 2, clip)
    assert snd.frames.ndim == 2
    #
    # paste a mono clip into a stereo file
    snd.frames = numpy.array([[1, 1], [2, 2], [3, 3], [4, 4]])
    clip = numpy.array([22, 33])
    snd.paste(1, 3, clip)
    assert snd.frames.tolist() == [[1, 1], [22, 22], [33, 33], [4, 4]]
    snd.undo()
    assert snd.frames.tolist() == [[1, 1], [2, 2], [3, 3], [4, 4]]
    snd.paste(1, 1, clip)
    assert snd.frames.tolist() == [[1, 1], [22, 22], [33, 33],\
                                                        [2, 2], [3, 3], [4, 4]]
    # pasting in empty sound: keep it mono
    snd.frames = numpy.array([])
    snd.paste(1, 2, clip)
    assert snd.frames.ndim == 1

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
    #
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
    #
    # mix a stereo clip into a mono file
    snd.frames = numpy.array([1, 2, 3, 4])
    clip = numpy.array([[30, 10], [40, 20]])
    snd.mix(1, 3, clip)
    assert snd.frames.tolist() == [1, 22, 33, 4]
    #
    # mix a mono clip into a stereo file
    snd.frames = numpy.array([[1, 1], [2, 2], [3, 3], [4, 4]])
    clip = numpy.array([20, 30])
    snd.mix(1, 3, clip)
    assert snd.frames.tolist() == [[1, 1], [22, 22], [33, 33], [4, 4]]

    # Do not crash when saving with None as filename
    snd = Sound()
    try:
        snd.save()
    except:
        print "OK"
    else:
        assert False

    # expand user symbol
    from gum.lib import mock
    def fake_sndfile(filename):
        assert '~' not in filename
        return mock.Fake()
    sndfile = pysndfile.sndfile
    pysndfile.sndfile = fake_sndfile
    Sound("~/sound.wav")
    pysndfile.sndfile = sndfile

if __name__ == '__main__':
    testSound()
