# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import gtk
import cairo

# -- Base classes for drawing sound visualization.
#
# CairoWidget, LayeredCairoWidget, and LayeredGraphView are defined as
# successive subclasses only for code clarity. Everything could as
# well be stuck in LayeredGraphView.
#
class CairoWidget(gtk.DrawingArea):

    __gsignals__ = {"expose-event": "override"}

    def __init__(self):
        super(CairoWidget, self).__init__()
    
    def do_expose_event(self, event):
        context = self.window.cairo_create()
        context.rectangle(event.area.x, event.area.y,
                          event.area.width, event.area.height)
        context.clip()
        width, height = self.window.get_size()
        self.draw(context, width, height)

    def redraw(self):
        # queue_draw() emits an expose event. Double buffering is used
        # automatically in the expose event handler.
        self.queue_draw()

    def draw(self, context, width, height):
        """Must be overriden to draw to the cairo context."""
        pass


class LayeredCairoWidget(CairoWidget):
    """A widget with several layers.

    This widget paints itself by successively passing its context to
    layer objects. The draw() method of a layer object must paint to
    the context.
    
    """
    def __init__(self):
        super(LayeredCairoWidget, self).__init__()
        self.layers = []
        
    def draw(self, context, width, height):
        for layer in self.layers:
            layer.draw(context, width, height)


class LayeredGraphView(LayeredCairoWidget):
    """A layered widget dedicated to a Graph object.
    
    Every time the widget is resized, the new width is passed to the
    Graph object.

    """
    def __init__(self, graph):
        super(LayeredGraphView, self).__init__()
        self._graph = graph
        self.connect("size_allocate", self.resized)

    def resized(self, widget, rect):
        self._graph.set_width(rect.width)


# -- The sound visualization widget, composed of several layers:
#
#    * waveform
#    * selection
#    * cursor
#
class GraphView(LayeredGraphView):
    """Sound visualization widget for the main window.

    * Two graphical layers: the waveform and the selection.
    * Mouse event listeners act on models (scroll and selection).

    """
    def __init__(self, graph, selection, cursor):
        super(GraphView, self).__init__(graph)
        self._graph = graph
        self._selection = selection
        self.layers.append(WaveformLayer(self, graph))
        self.layers.append(SelectionLayer(self, selection))
        self.layers.append(CursorLayer(self, cursor))
        MouseSelection(self, selection, cursor)
        MouseScroll(self, graph)


# -- Layers that can be added to LayeredGraphview.
#
class WaveformLayer(object):
    """A layer for LayeredGraphView.

    It paints the graph (the waveform). The cairo surface is cached,
    it is redrawn only when graph has changed.

    """
    def __init__(self, layered, graph):
        self._layered = layered
        self._graph = graph
        self._cache = None
        self.wavecolor = 0.0, 0.47058823529411764, 1.0
        layered.add_events(gtk.gdk.SCROLL_MASK)
        graph.changed.connect(self.update)

    def update(self):
        self._cache = None
        self._layered.redraw()

    def draw_channel(self, values, surface, width, height):
        "Draw one sound channel on a cairo surface."
        c = cairo.Context(surface)

        # Line at zero
        c.set_line_width(1)
        c.set_source_rgb(0.2, 0.2, 0.2)
        c.move_to(0, round(height / 2) + 0.5)
        c.line_to(width, round(height / 2) + 0.5)
        c.stroke()

        # Waveform
        c.set_source_rgb(*self.wavecolor)
        for i, (mini, maxi) in enumerate(values):
            # -1 <= mini <= maxi <= 1
            x = i
            ymin = round((-mini * 0.5 + 0.5) * height)
            ymax = round((-maxi * 0.5 + 0.5) * height)
            if ymin == ymax:
                # Fill one pixel 
                c.rectangle(x, ymin, 1, 1)
                c.fill()
            else:
                # Draw a line from min to max
                c.move_to(x + 0.5, ymin)
                c.line_to(x + 0.5, ymax)
                c.stroke()
        
    def draw(self, context, width, height):
        "Draw all sound channels."
        if not self._cache:
            surface = context.get_target()
            self._cache = surface.create_similar(cairo.CONTENT_COLOR,
                                                 width, height)
            c = cairo.Context(self._cache)
            channels = self._graph.channels()
            numchan = len(channels)
            for i in range(numchan):
                s = surface.create_similar(cairo.CONTENT_COLOR,
                                           width, height / numchan)
                self.draw_channel(channels[i], s, width, height / numchan)
                c.set_source_surface(s, 0, (height / numchan) * i)
                c.set_operator(cairo.OPERATOR_ATOP)
                c.paint()
                
        context.set_source_surface(self._cache, 0, 0)
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.paint()


class SelectionLayer(object):
    """A layer for LayeredGraphView.

    It highlights the selected area. It also listens to mouse events
    and changes the selection accordingly. The cairo surface is
    cached, it is redrawn only when selection has changed.

    """
    def __init__(self, layered, selection):
        self._layered = layered
        self._cache = None
        self._selection = selection
        self._selection.changed.connect(self.update)

    def update(self):
        self._cache = None
        self._layered.redraw()

    def draw(self, context, width, height):
        if not self._cache:
            surface = context.get_target()
            self._cache = surface.create_similar(cairo.CONTENT_COLOR_ALPHA,
                                                 width, height)
            c = cairo.Context(self._cache)
            start, end = self._selection.pixels()

            if start != end:
                # darken everything ...
                c.set_source_rgba(0, 0, 0, 0.5)
                c.paint()

                # ... then clear selection
                c.set_operator(cairo.OPERATOR_CLEAR)
                c.rectangle(start, 0, end - start, height)
                c.fill()
            
        context.set_source_surface(self._cache, 0, 0)
        context.set_operator(cairo.OPERATOR_OVER)
        context.paint()

class CursorLayer(object):

    def __init__(self, layered, cursor):
        self._layered = layered
        self._cache = None
        self._cursor = cursor
        self._cursor.changed.connect(self.update)
        self._height = None
        self.rgba = (1, 1, 1, 0.5)

    def update(self):
        self._layered.redraw() # called in all layers !

    def draw(self, context, width, height):
        if height != self._height:
            self._height = height
            surface = context.get_target()
            self._cache = surface.create_similar(cairo.CONTENT_COLOR_ALPHA,
                                                 1, height)
            c = cairo.Context(self._cache)
            c.set_source_rgba(*self.rgba)
            c.set_line_width(1)
            c.move_to(0.5, 0)
            c.line_to(0.5, height)
            c.stroke()

        x = self._cursor.pixel()
        context.set_source_surface(self._cache, x, 0)
        context.set_operator(cairo.OPERATOR_OVER)
        context.paint()


# -- Mouse event listeners that act on models.
#
class MouseScroll(object):
    """Listens for mouse wheel events and scroll a graph.

    Must be attached to a gtk.Widget and a Graph.

    """
    def __init__(self, widget, graph):
        self._graph = graph
        widget.connect("scroll_event", self.scroll_event)

    def scroll_event(self, widget, event):
        if event.direction in (gtk.gdk.SCROLL_UP, gtk.gdk.SCROLL_LEFT):
            self._graph.scroll_left()
        elif event.direction in (gtk.gdk.SCROLL_DOWN, gtk.gdk.SCROLL_RIGHT):
            self._graph.scroll_right()

class MouseSelection(object):
    """Listens for mouse events and select graph area.

    Must be attached to a gtk.Widget, a Selection and a Cursor.

    """
    def __init__(self, widget, selection, cursor):
        self._selection = selection
        self._cursor = cursor
        self.pressed = False
        widget.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                          gtk.gdk.BUTTON_RELEASE_MASK |
                          gtk.gdk.POINTER_MOTION_MASK |
                          gtk.gdk.POINTER_MOTION_HINT_MASK)
        widget.connect("button_press_event", self.button_press)
        widget.connect("button_release_event", self.button_release)
        widget.connect("motion_notify_event", self.motion_notify)
        
    def button_press(self, widget, event):
        if event.button == 1:
            self.pressed = True
            self._selection.start_selection(event.x)

    def motion_notify(self, widget, event):
        if self.pressed:
            x = event.window.get_pointer()[0]
            self._selection.end_selection(x)
            
    def button_release(self, widget, event):
        if event.button == 1:
            start, end = self._selection.get()
            self._cursor.set_frame(start)
            self.pressed = False

# -- Horizontal scrollbar, subclassed to control a Graph object.
#
class GraphScrollbar(gtk.HScrollbar):
    """An horizontal scrollbar tied to a Graph.

    Acts on a graph object and is updated when the graph
    object changes.

    """
    def __init__(self, graph):
        self._adjustment = gtk.Adjustment(0, 0, 1, 0.1, 0, 1)
        super(GraphScrollbar, self).__init__(self._adjustment)
        self._graph = graph
        self._graph.changed.connect(self.update_scrollbar)
        self.connect("value-changed", self.update_model)
        
        # When the scrollbar or the graph model changes, this
        # attribute must be set to True to avoid infinite feedback
        # between them. Example of what happens otherwise: scrollbar
        # changes --> graph changes --> scrollbar changes --> ...
        self.inhibit = False

    def update_model(self, widget):
        """Changes the model.

        Called when the scrollbar has been moved by the user.

        """
        if not self.inhibit:
            self.inhibit = True
            self._graph.move_to(self._adjustment.value)
            self.inhibit = False
        
    def update_scrollbar(self):
        """Changes the scrollbar.

        Called when the model has changed.

        """
        if not self.inhibit:
            self.inhibit = True
            length = self._graph.numframes()
            start, end = self._graph.view()
            if start != end:
                self._adjustment.upper = length
                self._adjustment.value = start
                self._adjustment.page_size = (end - start)
            else:
                # empty sound
                self._adjustment.upper = 1
                self._adjustment.value = 0
                self._adjustment.page_size = 1
            self.inhibit = False


# -- Tests

if __name__ == '__main__':
    from mock import Mock, Fake

    def test_layered():

        def randomized():
            from random import random        
            channels = [[((random() - 0.5) * 2, (random() - 0.5) * 2)
                       for i in xrange(500)]]
            graph = Mock({"channels": channels,
                          "set_width": None,
                          "frames_info": (0, 0, 0)})
            graph.changed = Fake()
            layered = LayeredGraphView(graph)
            layered.layers.append(WaveformLayer(layered, graph))
            return layered

        def sine():
            from math import sin
            sine = [sin(2 * 3.14 * 0.01 * x) for x in xrange(500)]
            channels = [[(i, i) for i in sine]]
            graph = Mock({"channels": channels, "set_width": None,
                          "frames_info": (0, 0, 0)})
            graph.changed = Fake()
            layered = LayeredGraphView(graph)
            layered.layers.append(WaveformLayer(layered, graph))
            return layered

        def sines():
            from math import sin
            sine = [sin(2 * 3.14 * 0.01 * x) for x in xrange(500)]
            channels = [[(i, i) for i in sine], [(i, i) for i in sine]]

            graph = Mock({"channels": channels, "set_width": None,
                          "frames_info": (0, 0, 0)})
            graph.changed = Fake()
            layered = LayeredGraphView(graph)
            layered.layers.append(WaveformLayer(layered, graph))
            return layered

        def selection():
            graph = Mock({"channels": [], "set_width": None,
                          "frames_info": (0, 0, 0)})
            graph.changed = Fake()
            selection = Mock({"pixels": (20, 100)})
            selection.changed = Fake()
            layered = LayeredGraphView(graph)
            layered.layers.append(SelectionLayer(layered, selection))
            return layered

        def cursor():
            graph = Mock({"channels": [], "set_width": None,
                          "frames_info": (0, 0, 0)})
            class Cursor: pass
            cursor = Cursor()
            cursor.changed = Fake()
            cursor.pixel = lambda: 50
            layered = LayeredGraphView(graph)
            cursorlayer = CursorLayer(layered, cursor)
            cursorlayer.rgba = (1, 0, 0, 1)
            layered.layers.append(cursorlayer)
            return layered

        layereds = [randomized(), sine(), sines(), selection(), cursor()]

        for layered in layereds:
            window = gtk.Window()
            window.resize(500, 200)
            window.connect("delete-event", gtk.main_quit)
            window.add(layered)
            window.show_all()
            gtk.main()

    test_layered()
