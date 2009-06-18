import numpy 
from copy import copy

effects = {}

class Effect(object):
    """Base class for sound effects. 

    apply() and revert() must be overridden.

    """
    def __init__(self, sound, selection):
        self.sound = sound
        self.selection = selection

    def apply(self):
        """Apply effect to sound.frames."""
        pass

    def revert(self):
        """Revert the changes made by apply()."""
        pass


class Reverse(Effect):
    """Reverse the selected part of sound."""
    def apply(self):
        start, end = self.selection
        rev = numpy.flipud(copy(self.sound.frames[start:end]))
        self.sound.frames[start:end] = rev

    def revert(self):
        self.apply()    


class Normalize(Effect):
    """Normalize the selected part of sound."""
    def apply(self):
        start, end = self.selection
        self.clip = copy(self.sound.frames[start:end])
        M = abs(self.sound.frames[start:end]).max()
        factor = 1. / M
        self.sound.frames[start:end] = self.sound.frames[start:end] * factor

    def revert(self):
        start, end = self.selection
        self.sound.frames[start:end] = self.clip


# Register effects
effects['reverse'] = Reverse
effects['normalize'] = Normalize


# Tests
if __name__ == '__main__':
    from edit import Sound
    import numpy

    # test reverse()
    snd = Sound()
    snd.frames = numpy.array(range(10))
    fx = Reverse(snd, (3, 6))
    fx.apply()
    assert snd.frames.tolist() == [0, 1, 2, 5, 4, 3, 6, 7, 8, 9]
    fx.revert()
    assert snd.frames.tolist() == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    snd.frames = numpy.array(zip(range(8), range(8)))
    fx = Reverse(snd, (3, 6))
    fx.apply()
    assert snd.frames.tolist() == [[0, 0], [1, 1], [2, 2], [5, 5],
                                  [4, 4], [3, 3], [6, 6], [7, 7]]

    # test normalize
    snd = Sound()
    snd.frames = numpy.array([0, 0.5])
    fx = Normalize(snd, (0, 2))
    fx.apply()
    assert snd.frames.tolist() == [0, 1]
    fx.revert()
    assert snd.frames.tolist() == numpy.array([0, 0.5]).tolist()

    snd.frames = numpy.array([0, -0.5])
    fx = Normalize(snd, (0, 2))
    fx.apply()
    assert snd.frames.tolist() == [0, -1]
    fx.revert()
    assert snd.frames.tolist() == numpy.array([0, -0.5]).tolist()
