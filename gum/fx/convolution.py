from gum.controllers import effect
from gum.models import clipboard, sound
import numpy

def nextpow2(n):
    """Return the smallest p such as 2 ** p >= n """
    p = int(numpy.floor(numpy.log2(n)))
    if 2 ** p < n:
        p = p + 1
    return p


def ola_fftconvolve(x, h):
    # http://www.dspdesignline.com/showArticle.jhtml?articleID=199901970
    Nfft = 2 ** nextpow2(len(h))
    H = numpy.fft.fft(h, Nfft)
    lslice = Nfft - len(h) + 1 # because lslice + len(h) - 1 == Nfft
    numslices = numpy.ceil(float(len(x)) / lslice)
    y = numpy.zeros(numslices * lslice + len(h) - 1)
    start = 0
    while start < len(x):
        slice = x[start:start + lslice]
        X = numpy.fft.fft(slice, Nfft)
        Y = X * H
        y[start:start+Nfft] += numpy.real(numpy.fft.ifft(Y, Nfft))
        start = start + lslice
    return y


def convolution(sound, start, end):

    x = sound.frames
    h = clipboard.clip

    numchan = max(x.ndim, h.ndim)
    if numchan == 1:
        y = ola_fftconvolve(x[start:end], h)
    else:
        y = []
        if h.ndim == 1:
            #! H will be computed two times !
            h = sound.mix_channels_auto(h, 2)
        if x.ndim == 1:
            x = sound.mix_channels_auto(x, 2)
        h = h.transpose()
        x = x.transpose()
        for nchan in range(2):
            tmp = ola_fftconvolve(x[nchan][start:end], h[nchan])
            y.append(tmp)
        y = numpy.array(y)
        y = y.transpose()

    # normalize
    if y.any():
        M = abs(y).max()
        factor = 1. / M
        y = y * factor

    l = len(sound.frames)
    sound.paste(0, l, y)


effect.effects['Convolve with clipboard'] = convolution
