import numpy
cimport numpy

DTYPE = numpy.float64
ctypedef numpy.float64_t DTYPE_t

def svf(numpy.ndarray[DTYPE_t, ndim=1] x not None,
        float f, float damping, int samplerate):
    """State variable filters. DAFX book, Section 2.2, page 36."""
    cdef float F
    cdef float Q
    cdef Py_ssize_t l
    cdef numpy.ndarray[DTYPE_t, ndim=1] yh
    cdef numpy.ndarray[DTYPE_t, ndim=1] yb
    cdef numpy.ndarray[DTYPE_t, ndim=1] yl
    cdef Py_ssize_t n
    
    F = 2 * numpy.sin(numpy.pi * f / samplerate)
    Q = 2 * damping
    l = len(x)
    yh = numpy.zeros(l, dtype=DTYPE)
    yb = numpy.zeros(l, dtype=DTYPE)
    yl = numpy.zeros(l, dtype=DTYPE)

    n = 0
    while n < l:
        yh[n] = x[n] - yl[n-1] - Q * yb[n-1]
        yb[n] = F * yh[n] + yb[n-1]
        yl[n] = F * yb[n] + yl[n-1]
        n = n + 1

    return yh, yb, yl
