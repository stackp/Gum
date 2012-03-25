#include <Python.h>

typedef struct {
  PyObject_HEAD
  void *ctx;
} PycairoContext;

void cairo_move_to (void *cr, double x, double y);
void cairo_line_to (void *cr, double x, double y);
void cairo_rectangle(void *cr, double x, double ymin,
                     double w, double h);
void cairo_set_source_rgb (void *cr, double r, double g, double b);
void cairo_stroke (void *cr);
void cairo_fill (void *cr);
void cairo_set_line_width(void *cr, double w);
