import gtk
import cairo

# -- Base classes for painting sound visualization.
#
# Defined step by step only for code clarity. Everything could as well
# be stuck in one class.

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

    def update(self):
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
    """A layered widget dedicated to paint data from a Graph
    object.
    
    As soon as it knows its width, it gives it to the Graph
    object.

    """
    def __init__(self, graph):
        super(LayeredGraphView, self).__init__()
        self._graph = graph
        self.connect("size_allocate", self.resize)

    def resize(self, widget, rect):
        self._graph.set_width(rect.width)


# -- Aah, beautiful sound visualization widget.

class GraphView(LayeredGraphView):
    """Sound visualization widget for the main window.

    * Two graphical layers: the waveform and the selection.
    * Mouse event listeners act on models (scroll and selection).

    """
    def __init__(self, graph, selection):
        super(GraphView, self).__init__(graph)
        self._graph = graph
        self._selection = selection
        self.layers.append(WaveformLayer(self, graph))
        self.layers.append(SelectionLayer(self, graph, selection))
        MouseSelection(self, selection)
        MouseScroll(self, graph)


# -- The layers that can be added to LayeredGraphview.

class WaveformLayer(object):
    """A layer for LayeredGraphView.

    It paints the graph (the waveform). The cairo surface is cached,
    it is redrawn only when graph has changed.

    """
    def __init__(self, layered, graph):
        self._layered = layered
        self._graph = graph
        self._cache = None
        layered.add_events(gtk.gdk.SCROLL_MASK)
        graph.changed.connect(self.update)

    def update(self):
        self._cache = None
        self._layered.update()
        
    def draw(self, context, width, height):
        if not self._cache:
            surface = context.get_target()
            self._cache = surface.create_similar(cairo.CONTENT_COLOR,
                                                 width, height)
            c = cairo.Context(self._cache)

            # black background
            c.set_source_rgb(0, 0, 0)
            c.paint()

            # line at zero
            c.set_line_width(1)
            c.set_source_rgb(0.2, 0.2, 0.2)
            c.move_to(0, round(height / 2) + 0.5)
            c.line_to(width, round(height / 2) + 0.5)
            c.stroke()

            # waveform
            c.set_source_rgb(0, 0.9, 0)
            overview = self._graph.get_values()
            for i, value in enumerate(overview):
                x = i
                y = round((-value * 0.5 + 0.5) * height)
                #c.rectangle(x, y, 1, 1)
                #c.fill()
                c.move_to(x + 0.5, 0.5 * height + 0.5)
                c.line_to(x + 0.5, y + 0.5)
                c.stroke()

        context.set_source_surface(self._cache, 0, 0)
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.paint()

class SelectionLayer(object):
    """A layer for LayeredGraphView.

    It highlights the selected area. It also listens to mouse events
    and changes the selection accordingly. The cairo surface is
    cached, it is redrawn only when selection has changed.

    """
    def __init__(self, layered, graph, selection):
        self._layered = layered
        self._graph = graph
        self._cache = None
        self._selection = selection
        self._selection.changed.connect(self.update)
        layered.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                           gtk.gdk.BUTTON_RELEASE_MASK |
                           gtk.gdk.POINTER_MOTION_MASK |
                           gtk.gdk.POINTER_MOTION_HINT_MASK)

    def update(self):
        self._cache = None
        self._layered.update()

    def draw(self, context, width, height):
        if not self._cache:
            surface = context.get_target()
            self._cache = surface.create_similar(cairo.CONTENT_COLOR_ALPHA,
                                                 width, height)
            c = cairo.Context(self._cache)
            start, end = self._selection.get_selection()

            if start != end:

                if start > end:
                    start, end = end, start
                    
                # darken everything ...
                c.set_source_rgba(0, 0, 0, 0.75)
                c.paint()

                # ... then clear selection
                c.set_operator(cairo.OPERATOR_CLEAR)
                c.rectangle(start + 0.5, 0, end - start + 0.5, height)
                c.fill()


            # cursors
            c.set_operator(cairo.OPERATOR_ADD)
            c.set_line_width(1)
            c.set_source_rgba(1, 1, 1, 0.7)
            c.move_to(start + 0.5, 0)
            c.line_to(start + 0.5, height)
            c.move_to(end + 0.5, 0)
            c.line_to(end + 0.5, height)
            c.stroke()
            
        context.set_source_surface(self._cache, 0, 0)
        context.set_operator(cairo.OPERATOR_OVER)
        context.paint()


# -- Mouse event listeners that act on models.

class MouseScroll(object):
    """Listens for mouse wheel events and scroll a graph

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
    """Listens for mouse events and select graph area

    Must be attached to a gtk.Widget and a Graph.

    """
    def __init__(self, widget, selection):
        self._selection = selection
        self.pressed = False
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
            self.pressed = False


# -- An horizontal scrollbar, derived to control a graph model.

class GraphScrollbar(gtk.HScrollbar):
    """An horizontal scrollbar that acts on a Graph.

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
            self._graph.view_starts_at(self._adjustment.value)
            self.inhibit = False
        
    def update_scrollbar(self):
        """Changes the scrollbar.

        Called when the model has changed.

        """
        if not self.inhibit:
            self.inhibit = True
            length, start, end = self._graph.get_info()
            self._adjustment.upper = length
            self._adjustment.value = start
            self._adjustment.page_size = (end - start)
            self.inhibit = False


# -- Testing

if __name__ == '__main__':
    from mock import Mock, Fake
    
    def test_window():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)
        graph = Mock({"get_values": [v / 500. for v in xrange(500)],
                     "set_width": None,
                     "get_info": (0, 0, 0)})
        graph.changed = Fake()
        layered = LayeredGraphView(graph)
        layered.layers.append(WaveformLayer(layered, graph))
        window.add(layered)
        window.show_all()
        gtk.main()

    def test_rand():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)

        from random import random
        values = [(random() - 0.5) * 2 for i in xrange(500)]        
        graph = Mock({"get_values": values, "set_width": None,
                          "get_info": (0, 0, 0)})
        graph.changed = Fake()
        layered = LayeredGraphView(graph)
        layered.layers.append(WaveformLayer(layered, graph))
        window.add(layered)
        window.show_all()
        gtk.main()

    def test_sine():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)

        from math import sin
        sine = [sin(2 * 3.14 * 0.01 * x) for x in xrange(500)]
        graph = Mock({"get_values": sine, "set_width": None,
                          "get_info": (0, 0, 0)})
        graph.changed = Fake()
        layered = LayeredGraphView(graph)
        layered.layers.append(WaveformLayer(layered, graph))
        window.add(layered)
        window.show_all()
        gtk.main()

    def test_selection():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)

        graph = Mock({"get_values": [], "set_width": None,
                          "get_info": (0, 0, 0)})
        graph.changed = Fake()
        selection = Mock({"get_selection": (20, 100)})
        selection.changed = Fake()
        layered = LayeredGraphView(graph)
        layered.layers.append(SelectionLayer(layered, graph, selection))
        window.add(layered)
        window.show_all()
        gtk.main()

    test_window()
    test_rand()
    test_sine()
    test_selection()
