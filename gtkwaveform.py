import gtk
import cairo
import gobject

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
    """A layered widget dedicated to paint data from a GraphData
    object.
    
    As soon as it knows its width, it gives it to the GraphData
    object.

    """
    def __init__(self, graphdata):
        super(LayeredGraphView, self).__init__()
        self._graphdata = graphdata
        self.connect("size_allocate", self.resize)

    def resize(self, widget, rect):
        self._graphdata.set_width(rect.width)


class WaveformLayer(object):
    """A layer for LayeredGraphView.

    It paints the graph (the waveform). The cairo surface is cached,
    it is redrawn only when graphdata has changed.

    """
    def __init__(self, layered, graphdata):
        self._layered = layered
        self._graphdata = graphdata
        self._cache = None
        layered.add_events(gtk.gdk.SCROLL_MASK)
        graphdata.changed.connect(self.update)

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
            overview = self._graphdata.get_values()
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
    def __init__(self, layered, graphdata, selection):
        self._layered = layered
        self._graphdata = graphdata
        self.pressed = False
        self._cache = None
        self._selection = selection
        self._selection.changed.connect(self.update)
        layered.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                           gtk.gdk.BUTTON_RELEASE_MASK |
                           gtk.gdk.POINTER_MOTION_MASK |
                           gtk.gdk.POINTER_MOTION_HINT_MASK)
        self._layered.connect("button_press_event", self.button_press)
        self._layered.connect("button_release_event", self.button_release)
        self._layered.connect("motion_notify_event", self.motion_notify)

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
            c.set_source_rgba(1, 1, 1, 0.3)
            c.rectangle(start, 0, end - start, height)
            c.fill()
        context.set_source_surface(self._cache, 0, 0)
        context.set_operator(cairo.OPERATOR_OVER)
        context.paint()

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

class SelectableWaveform(LayeredGraphView):

    def __init__(self, graphdata, selection):
        super(SelectableWaveform, self).__init__(graphdata)
        self._graphdata = graphdata
        self._selection = selection
        self.layers.append(WaveformLayer(self, graphdata))
        self.layers.append(SelectionLayer(self, graphdata, selection))

class ScrolledWaveform(gtk.VBox):
    """A waveform with a scrollbar.

    This widget groups a Waveform widget and a horizontal
    scrollbar. Both act on the same graphdata object. Both are updated
    when the graphdata object changes.

    """
    def __init__(self, graphdata, selection):
        super(gtk.VBox, self).__init__()
        self._waveform = SelectableWaveform(graphdata, selection)
        self._adjustment = gtk.Adjustment(0, 0, 1, 0.1, 0, 1)
        self._hscrollbar = gtk.HScrollbar(self._adjustment)
        self._graphdata = graphdata
        self.pack_start(self._waveform, expand=True, fill=True)
        self.pack_start(self._hscrollbar, expand=False, fill=False)
        self._hscrollbar.connect("value-changed", self.update_model)
        self._graphdata.changed.connect(self.update_scrollbar)
        self.connect("scroll_event", self.scroll_event)
        
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
            self._graphdata.view_starts_at(self._adjustment.value)
            self.inhibit = False
        
    def update_scrollbar(self):
        """Changes the scrollbar.

        Called when the model has changed.

        """
        if not self.inhibit:
            self.inhibit = True
            length, start, end = self._graphdata.get_info()
            self._adjustment.upper = length
            self._adjustment.value = start
            self._adjustment.page_size = (end - start)
            self.inhibit = False

    def scroll_event(self, widget, event):
        if event.direction in (gtk.gdk.SCROLL_UP, gtk.gdk.SCROLL_LEFT):
            self._graphdata.scroll_left()
        elif event.direction in (gtk.gdk.SCROLL_DOWN, gtk.gdk.SCROLL_RIGHT):
            self._graphdata.scroll_right()


if __name__ == '__main__':
    from mock import Mock, Fake
    
    def test_window():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)
        graphdata = Mock({"get_values": [v / 500. for v in xrange(500)],
                     "set_width": None,
                     "get_info": (0, 0, 0)})
        graphdata.changed = Fake()
        layered = LayeredGraphView(graphdata)
        layered.layers.append(WaveformLayer(layered, graphdata))
        window.add(layered)
        window.show_all()
        gtk.main()

    def test_rand():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)

        from random import random
        values = [(random() - 0.5) * 2 for i in xrange(500)]        
        graphdata = Mock({"get_values": values, "set_width": None,
                          "get_info": (0, 0, 0)})
        graphdata.changed = Fake()
        layered = LayeredGraphView(graphdata)
        layered.layers.append(WaveformLayer(layered, graphdata))
        window.add(layered)
        window.show_all()
        gtk.main()

    def test_sine():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)

        from math import sin
        sine = [sin(2 * 3.14 * 0.01 * x) for x in xrange(500)]
        graphdata = Mock({"get_values": sine, "set_width": None,
                          "get_info": (0, 0, 0)})
        graphdata.changed = Fake()
        layered = LayeredGraphView(graphdata)
        layered.layers.append(WaveformLayer(layered, graphdata))
        window.add(layered)
        window.show_all()
        gtk.main()

    def test_selection():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)

        graphdata = Mock({"get_values": [], "set_width": None,
                          "get_info": (0, 0, 0)})
        graphdata.changed = Fake()
        selection = Mock({"get_selection": (20, 100)})
        selection.changed = Fake()
        layered = LayeredGraphView(graphdata)
        layered.layers.append(SelectionLayer(layered, graphdata, selection))
        window.add(layered)
        window.show_all()
        gtk.main()

    test_window()
    test_rand()
    test_sine()
    test_selection()
