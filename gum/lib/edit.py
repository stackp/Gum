import numpy
from scikits import samplerate


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


if __name__ == "__main__":

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

