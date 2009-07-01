import numpy 
from copy import copy

effects = {}

def reverse(x):
    return numpy.flipud(x)

def normalize(x):
    y = copy(x)
    if len(x) > 0:
        M = abs(x).max()
        if M != 0:
            factor = 1. / M
            y = y * factor
    return y

def negate(x):
    return -x


def mkfx_overwrite_selection(function):
    def apply(sound, start, end):
        x = sound.frames[start:end]
        y = function(x)
        sound.paste(start, end, y)
    return apply

# Register effects
effects['Reverse'] = mkfx_overwrite_selection(reverse)
effects['Normalize'] = mkfx_overwrite_selection(normalize)
effects['Negate'] = mkfx_overwrite_selection(negate)

# Tests
if __name__ == '__main__':
    from edit import Sound
    import numpy

    # test reverse()
    fx = effects['Reverse']

    snd = Sound()
    snd.frames = numpy.array(range(10))
    fx(snd, 3, 6)
    assert snd.frames.tolist() == [0, 1, 2, 5, 4, 3, 6, 7, 8, 9]
    snd.undo()
    assert snd.frames.tolist() == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    snd.frames = numpy.array(zip(range(8), range(8)))
    fx(snd, 3, 6)
    assert snd.frames.tolist() == [[0, 0], [1, 1], [2, 2], [5, 5],
                                  [4, 4], [3, 3], [6, 6], [7, 7]]

    # test normalize
    fx = effects['Normalize']

    snd = Sound()
    snd.frames = numpy.array([0, 0.5, 0.2])
    fx(snd, 0, 2)
    assert snd.frames.tolist() == [0, 1, 0.2]
    snd.undo()
    assert snd.frames.tolist() == [0, 0.5, 0.2]

    snd.frames = numpy.array([0, -0.5])
    fx(snd, 0, 2)
    assert snd.frames.tolist() == [0, -1]
    snd.undo()
    assert snd.frames.tolist() == [0, -0.5]

    snd.frames = numpy.array([0, 0, 0, 0, 0])
    fx(snd, 0, 5)
    assert snd.frames.tolist() == [0, 0, 0, 0, 0]
    snd.undo()
    assert snd.frames.tolist() == [0, 0, 0, 0, 0]

    snd.frames = numpy.array([])
    fx(snd, 0, 1)
    assert snd.frames.tolist() == []
    snd.undo()
    assert snd.frames.tolist() == []
