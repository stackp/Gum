#cython: boundscheck=False

cdef extern from "math.h":
    double round (double x) nogil

cdef extern from "fast.h":
    ctypedef struct PycairoContext:
      void *ctx
    void cairo_move_to (void *cr, double x, double y) nogil
    void cairo_line_to (void *cr, double x, double y) nogil
    void cairo_rectangle(void *cr, double x, double ymin,
                         double w, double h) nogil
    void cairo_set_source_rgb (void *cr, double r, double g, double b) nogil
    void cairo_stroke (void *cr) nogil
    void cairo_fill (void *cr) nogil
    void cairo_set_line_width(void *cr, double w) nogil


def draw_channel(list values,
                 context,
                 float ystart, float width, float height):
    cdef PycairoContext *pcc
    cdef void *cr
    cdef double mini, maxi, x, ymin, ymax

    pcc = <PycairoContext *> context
    cr = pcc.ctx

    # Line at zero
    cairo_set_line_width(cr, 1)
    cairo_set_source_rgb(cr, 0.2, 0.2, 0.2)
    cairo_move_to(cr, 0, ystart + round(height / 2) + 0.5)
    cairo_line_to(cr, width, ystart + round(height / 2) + 0.5)
    cairo_stroke(cr)

    # Waveform
    cairo_set_source_rgb(cr, 0.0, 0.47058823529411764, 1.0)
    for x, (mini, maxi) in enumerate(values):
        with nogil:
            # -1 <= mini <= maxi <= 1
            # ystart <= ymin <= ymax <= ystart + height - 1
            ymin = ystart + round((-mini * 0.5 + 0.5) * (height - 1))
            ymax = ystart + round((-maxi * 0.5 + 0.5) * (height - 1))
            if ymin == ymax:
                # Fill one pixel
                cairo_rectangle(cr, x, ymin, 1, 1)
                cairo_fill(cr)
            else:
                # Draw a line from min to max
                cairo_move_to(cr, x + 0.5, ymin)
                cairo_line_to(cr, x + 0.5, ymax)
                cairo_stroke(cr)



import numpy
cimport numpy
DTYPE = numpy.float64
ctypedef numpy.float64_t DTYPE_t

def _condense(numpy.ndarray[DTYPE_t, ndim=1] data,
              int start, int width, float density):
    """Returns a list of (min, max) tuples.

    A density slices the data in "cells", each cell containing several
    frames. This function returns the min and max of each visible cell.

    """
    cdef Py_ssize_t i, j, a, b, l
    cdef double mini, maxi, x
    res = []
    l = len(data)
    for i in range(start, start + width):
        with nogil:
            a = <int> round(i * density)
            b = <int> round((i + 1) * density)
            if a >= l:
                break
            if b > l:
                b = l
            mini = data[a]
            maxi = data[a]
            for j in range(a, b):
                x = data[j]
                if x > maxi:
                    maxi = x
                if x < mini:
                    mini = x
        res.append((mini, maxi))
    return res
