# Gum sound editor (https://github.com/stackp/Gum)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import gtk
import gobject
import cairo
try:
    from gum import fast
except ImportError:
    HAVE_FAST = False
else:
    HAVE_FAST = True

# -- Base classes for drawing sound visualization.
#
# CairoWidget, LayeredCairoWidget, and LayeredGraphView are defined as
# successive subclasses only for code clarity. Everything could as
# well be stuck in LayeredGraphView.
#
class CairoWidget(gtk.DrawingArea):

    __gsignals__ = {"expose-event": "override"}

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self._redrawing = False

    def do_expose_event(self, event):
        context = self.window.cairo_create()
        context.rectangle(event.area.x, event.area.y,
                          event.area.width, event.area.height)
        context.clip()
        width, height = self.window.get_size()
        self.draw(context, width, height)
        self._redrawing = False

    def redraw(self):
        # queue_draw() emits an expose event. Double buffering is used
        # automatically in the expose event handler.
        if not self._redrawing:
            self._redrawing = True
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
            layer.stack(context, width, height)


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

    * Four graphical layers: background, waveform, selection, and cursor.
    * Mouse event listeners act on models (scroll, selection, middle-click).

    """

    __gsignals__ = {'selection-changed': (gobject.SIGNAL_RUN_LAST,
                                          gobject.TYPE_NONE,
                                          ())}

    def __init__(self, graph, selection, cursor):
        super(GraphView, self).__init__(graph)
        self.layers.append(BackgroundLayer(self, selection))
        self.layers.append(WaveformLayer(self, graph))
        self.layers.append(SelectionLayer(self, selection))
        self.layers.append(CursorLayer(self, cursor))
        MouseSelection(self, selection)
        MouseScroll(self, graph)
        MouseMiddleClick(self, graph)
        PointerStyle(self, selection)
        self.connect("destroy", self.on_destroy)

    def on_destroy(self, widget):
        # Lose the references to Layers objects, otherwise they do not
        # get garbage-collected. I suspect a strange interaction
        # between the gobject and the Python reference counting
        # systems.
        self.layers = []



# -- Layers that can be added to LayeredGraphview.
#

class Layer(object):
    """Base class for layers."""

    def __init__(self, layered):
        self._layered = layered

    def stack(self, context, width, height):
        """Paint the layer on top of the passed context."""
        context.set_operator(cairo.OPERATOR_OVER)
        self.draw(context, width, height)

    def update(self):
        self._layered.redraw()

    def draw(context, width, height):
        raise NotImplemented


class CachedLayer(Layer):
    """Implements surface caching."""
    
    def __init__(self, layered):
        self._layered = layered
        self._must_draw = True
        self._surface = None
        layered.connect("size_allocate", self.resized)

    def resized(self, widget, rect):
        self._surface = None
        self._must_draw = True

    def update(self):
        self._must_draw = True
        Layer.update(self)

    def stack(self, context, width, height):
        if self._surface is None:
            surface = context.get_target()
            self._surface = surface.create_similar(cairo.CONTENT_COLOR_ALPHA,
                                                   width, height)

        if self._must_draw:
            # clear the cached surface
            c = cairo.Context(self._surface)
            c.set_operator(cairo.OPERATOR_CLEAR)
            c.paint()
            c.set_operator(cairo.OPERATOR_OVER)
            self.draw(c, width, height)
            self._must_draw = False

        context.set_source_surface(self._surface, 0, 0)
        context.set_operator(cairo.OPERATOR_OVER)
        context.paint()
    

class WaveformLayer(CachedLayer):
    """A layer for LayeredGraphView.

    It paints the graph (the waveform).

    """
    def __init__(self, layered, graph):
        CachedLayer.__init__(self, layered)
        self._graph = graph
        self.wavecolor = 0.0, 0.47058823529411764, 1.0
        graph.changed.connect(self.update)

    def draw_channel(self, values, context, ystart, width, height):
        # Line at zero
        context.set_line_width(1)
        context.set_source_rgb(0.2, 0.2, 0.2)
        context.move_to(0, ystart + round(height / 2) + 0.5)
        context.line_to(width, ystart + round(height / 2) + 0.5)
        context.stroke()

        # Waveform
        context.set_source_rgb(*self.wavecolor)
        for x, (mini, maxi) in enumerate(values):
            # -1 <= mini <= maxi <= 1
            # ystart <= ymin <= ymax <= ystart + height - 1
            ymin = ystart + round((-mini * 0.5 + 0.5) * (height - 1))
            ymax = ystart + round((-maxi * 0.5 + 0.5) * (height - 1))
            if ymin == ymax:
                # Fill one pixel 
                context.rectangle(x, ymin, 1, 1)
                context.fill()
            else:
                # Draw a line from min to max
                context.move_to(x + 0.5, ymin)
                context.line_to(x + 0.5, ymax)
                context.stroke()

    if HAVE_FAST:
        draw_channel = fast.draw_channel

    def draw(self, context, width, height):
        channels = self._graph.channels()
        numchan = len(channels)
        for i in range(numchan):
            y = (height / numchan) * i
            self.draw_channel(channels[i], context, y, width, height / numchan)


class BackgroundLayer(Layer):
    """A layer for LayeredGraphView.

    """
    def __init__(self, layered, selection):
        Layer.__init__(self, layered)
        self._selection = selection
        self._selection.changed.connect(self.update)

    def draw(self, context, width, height):
        # Black background
        context.set_source_rgb(0, 0, 0)
        context.paint()

        # Selection background
        if self._selection.selected():
            context.set_source_rgb(0, 0, 0.2)
            start, end = self._selection.pixels()
            context.rectangle(start, 0, end - start, height)
            context.fill()


class SelectionLayer(Layer):
    """A layer for LayeredGraphView.

    It highlights the selected area.

    """
    def __init__(self, layered, selection):
        Layer.__init__(self, layered)
        self._selection = selection
        self._selection.changed.connect(self.update)

    def draw(self, context, width, height):
        if self._selection.selected():
            start, end = self._selection.pixels()
            context.set_source_rgba(0, 0, 0, 0.5)
            context.rectangle(0, 0, start, height)
            context.rectangle(end, 0, width - end, height)
            context.fill()


class CursorLayer(Layer):

    def __init__(self, layered, cursor):
        Layer.__init__(self, layered)
        self._cursor = cursor
        self._cursor.changed.connect(self.update)
        self.rgba = (1, 1, 1, 0.5)

    def draw(self, context, width, height):
        x = self._cursor.pixel()
        context.set_source_rgba(*self.rgba)
        context.set_line_width(1)
        context.move_to(x + 0.5, 0)
        context.line_to(x + 0.5, height)
        context.stroke()


# -- Mouse event listeners that act on models.
#

def near(x, y):
    return abs(x - y) < 10

class MouseScroll(object):
    """Listens for mouse wheel events and scroll a graph.

    Must be attached to a gtk.Widget and a Graph.

    """
    def __init__(self, widget, graph):
        self._graph = graph
        widget.add_events(gtk.gdk.SCROLL_MASK)
        widget.connect("scroll_event", self.scroll_event)

    def scroll_event(self, widget, event):
        MOD1 = event.state & gtk.gdk.MOD1_MASK
        LEFT = event.direction is gtk.gdk.SCROLL_LEFT
        RIGHT = event.direction is gtk.gdk.SCROLL_RIGHT
        UP = event.direction is gtk.gdk.SCROLL_UP
        DOWN = event.direction is gtk.gdk.SCROLL_DOWN

        if LEFT or (UP and MOD1):
            self._graph.scroll_left()
        elif RIGHT or (DOWN and MOD1):
            self._graph.scroll_right()
        elif UP:
            self._graph.zoom_in_on(event.x)
        elif DOWN:
            self._graph.zoom_out_on(event.x)


class MouseSelection(object):
    """Listens for mouse events and select graph area.

    Must be attached to a gtk.Widget and a Selection.

    """
    def __init__(self, widget, selection):
        self.widget = widget
        self._selection = selection
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
            x = event.x
            pstart, pend = self._selection.pixels()
            # a double click resumes selection.
            if event.type == gtk.gdk._2BUTTON_PRESS:
                self._selection.pin(x)
            # extend towards left
            elif self._selection.selected() and near(pstart, x):
                self._selection.move_start_to_pixel(x)
            # extend towards right
            elif self._selection.selected() and near(pend, x):
                self._selection.move_end_to_pixel(x)
            # start fresh selection
            else:
                self._selection.pin(x)

    def button_release(self, widget, event):
        if event.button == 1:
            self.pressed = False
            self.widget.emit("selection-changed")

    def motion_notify(self, widget, event):
        if self.pressed:
            x = event.window.get_pointer()[0]
            self._selection.extend(x)


class MouseMiddleClick(object):
    """Shift the wave display when the middle button is pressed."""
    def __init__(self, widget, graph):
        self.widget = widget
        self.graph = graph
        self.pressed = False
        widget.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                          gtk.gdk.BUTTON_RELEASE_MASK |
                          gtk.gdk.POINTER_MOTION_MASK |
                          gtk.gdk.POINTER_MOTION_HINT_MASK)
        widget.connect("button_press_event", self.button_press)
        widget.connect("button_release_event", self.button_release)
        widget.connect("motion_notify_event", self.motion_notify)

    def button_press(self, widget, event):
        if event.button == 2:
            self.pressed = True
            self._xlast = event.x

    def button_release(self, widget, event):
        if event.button == 2:
            self.pressed = False

    def motion_notify(self, widget, event):
        if self.pressed:
            x = event.window.get_pointer()[0]
            delta = self._xlast - x
            self._xlast = x
            start, _ = self.graph.view()
            self.graph.move_to(start + delta * self.graph.density)


class PointerStyle(object):
    """Change the pointer style.

    Show a hand when the middle click is pressed, otherwise show
    special cursors if the pointer is next to a selection bound.

    """
    LEFT_SIDE = gtk.gdk.Cursor(gtk.gdk.LEFT_SIDE)
    RIGHT_SIDE = gtk.gdk.Cursor(gtk.gdk.RIGHT_SIDE)
    HAND = gtk.gdk.Cursor(gtk.gdk.HAND1)

    def __init__(self, widget, selection):
        self.widget = widget
        self._selection = selection
        self.pressed = False
        widget.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                          gtk.gdk.BUTTON_RELEASE_MASK |
                          gtk.gdk.POINTER_MOTION_MASK |
                          gtk.gdk.POINTER_MOTION_HINT_MASK)
        widget.connect("button_press_event", self.button_press)
        widget.connect("button_release_event", self.button_release)
        widget.connect("motion_notify_event", self.motion_notify)

    def button_press(self, widget, event):
        if event.button == 2:
            self.pressed = True
            self.widget.window.set_cursor(self.HAND)

    def button_release(self, widget, event):
        if event.button == 2:
            self.pressed = False
            self.widget.window.set_cursor(None)

    def motion_notify(self, widget, event):
        if not self.pressed:
            style = None
            x = event.window.get_pointer()[0]
            if self._selection.selected():
                start, end = self._selection.pixels()
                if near(start, x):
                    style = self.LEFT_SIDE
                elif near(end, x):
                    style = self.RIGHT_SIDE
            self.widget.window.set_cursor(style)


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
                page_size = (end - start)
                self._adjustment.set_all(value = start,
                                         lower = 0,
                                         upper = length,
                                         page_increment = page_size,
                                         step_increment = page_size / 5.,
                                         page_size = page_size)
            else:
                # empty sound
                self._adjustment.set_all(value = 0,
                                         lower = 0,
                                         upper = 1,
                                         page_increment = 0,
                                         step_increment = 0,
                                         page_size = 1)
            self.inhibit = False


# -- Tests

if __name__ == '__main__':
    from gum.lib.mock import Mock, Fake

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

        def test_selection_layer(layerclass):
            graph = Mock({"channels": [], "set_width": None,
                          "frames_info": (0, 0, 0)})
            graph.changed = Fake()
            selection = Mock({"pixels": (20, 100), "selected": True})
            selection.changed = Fake()
            layered = LayeredGraphView(graph)
            layered.layers.append(layerclass(layered, selection))
            return layered

        def background():
            return test_selection_layer(BackgroundLayer)

        def selection():
            return test_selection_layer(SelectionLayer)

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

        layereds = [randomized(), sine(), sines(), selection(), cursor(),
                    background()]

        for layered in layereds:
            window = gtk.Window()
            window.resize(500, 200)
            window.connect("delete-event", gtk.main_quit)
            window.add(layered)
            window.show_all()
            gtk.main()

    test_layered()
