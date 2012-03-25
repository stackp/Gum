from gum.controllers.effect import effects
from gum.views import EffectDialog
import numpy
import functools

svf_index = {"High Pass": 0, "Band Pass": 1, "Low Pass": 2}

def svf(x, f, damping, samplerate):
    """State variable filters. DAFX book, Section 2.2, page 36."""
    F = 2 * numpy.sin(numpy.pi * f / samplerate)
    Q = 2 * damping

    yh = numpy.zeros(len(x))
    yb = numpy.zeros(len(x))
    yl = numpy.zeros(len(x))
    for n in range(len(x)):
        yh[n] = x[n] - yl[n-1] - Q * yb[n-1]
        yb[n] = F * yh[n] + yb[n-1]
        yl[n] = F * yb[n] + yl[n-1]
    return yh, yb, yl

try:
    from _svf import svf
except ImportError:
    print ("Warning: Optimized implementation of state variable filters not "
           "found, using pure python implementation instead.")

def process_each_channel(func, x):
    ndim = x.ndim
    if ndim == 1:
        x = [x]
    else:
        x = x.transpose()
    y = []
    for channel in x:
        y.append(func(channel))
    if ndim == 1:
        y = y[0]
    else:
        y = numpy.array(y).transpose()
    return y


def svf_fx(type, sound, start, end):

    def process(freq, damp):
        def apply(channel):
            filtered = svf(channel, freq, damp, sound.samplerate)
            i = svf_index[type]
            return filtered[i]
        y = process_each_channel(apply, sound.frames[start:end])
        sound.paste(start, end, y)

    def callback(parameters):
        freq = parameters['Frequency']
        damp = parameters['Damping']
        process(freq, damp)

    d = EffectDialog(type + ' State Variable Filter')
    d.add_slider('Frequency', 500, 0, 5000)
    d.add_slider('Damping', 0.5, 0.01, 3, 1)
    d.callback = callback
    return d


effects['Filter: High Pass'] = functools.partial(svf_fx, "High Pass")
effects['Filter: Band Pass'] = functools.partial(svf_fx, "Band Pass")
effects['Filter: Low Pass'] = functools.partial(svf_fx, "Low Pass")
