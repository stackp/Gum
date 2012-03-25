from gum.controllers import effect
from gum.views import EffectDialog
import numpy

nbits_last = 8

def bitcrush(x, nbits=4):
    maxamp = 2 ** int(nbits) / 2
    y = numpy.array(x * maxamp, dtype='int16')
    z = numpy.array(y, dtype='float64') / maxamp
    return z

def bitcrusher(sound, start, end):

    def process(nbits):
        y = bitcrush(sound.frames[start:end], nbits)
        sound.paste(start, end, y)

    def callback(parameters):
        nbits = parameters['Bit Width']
        global nbits_last
        nbits_last = nbits
        process(nbits)

    d = EffectDialog('BitCrusher')
    global nbits_last
    d.add_slider('Bit Width', nbits_last, 2, 12)
    d.callback = callback

    return d

effect.effects['Bit Crusher'] = bitcrusher
