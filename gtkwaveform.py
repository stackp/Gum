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

    def draw(self, context, width, height):
        """Must be overriden to draw to the cairo context."""
        pass

class Waveform(CairoWidget):

    def __init__(self, graphdata):
        super(Waveform, self).__init__()
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK|gtk.gdk.SCROLL_MASK)
        self.connect("button_press_event", self.button_press)
        self.connect("scroll_event", self.scroll_event)
        self.connect("size_allocate", self.resize)
        self._graphdata = graphdata
        self._graphdata.changed.connect(self.redraw)

    def resize(self, widget, rect):
        self._graphdata.set_width(rect.width)
        
    def draw(self, context, width, height):
        # black background
        context.set_source_rgb(0, 0, 0)
        context.paint()

        # line at zero
        context.set_line_width(1)
        context.set_source_rgb(0.2, 0.2, 0.2)
        context.move_to(0, round(height / 2) + 0.5)
        context.line_to(width, round(height / 2) + 0.5)
        context.stroke()

        # waveform
        context.set_source_rgb(0, 0.9, 0)
        overview = self._graphdata.get_values()
        for i, value in enumerate(overview):
            x = i
            y = round((-value * 0.5 + 0.5) * height)
            #context.rectangle(x, y, 1, 1)
            #context.fill()
            context.move_to(x + 0.5, 0.5 * height + 0.5)
            context.line_to(x + 0.5, y + 0.5)
            context.stroke()

    def redraw(self):
        # queue_draw() emits an expose event. Double buffering is used
        # automatically in the expose event handler.
        self.queue_draw()

    def button_press(self, widget, event):
        print event.button

    def scroll_event(self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self._graphdata.scroll_left()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self._graphdata.scroll_right()

class ScrolledWaveform(gtk.VBox):
    """A waveform with a scrollbar.

    This widget groups a Waveform widget and a horizontal
    scrollbar. Both act on the same graphdata object. Both are updated
    when the graphdata object changes.

    """
    def __init__(self, graphdata):
        super(gtk.VBox, self).__init__()
        self._waveform = Waveform(graphdata)
        self._adjustment = gtk.Adjustment(0, 0, 1, 0.1, 0, 1)
        self._hscrollbar = gtk.HScrollbar(self._adjustment)
        self._graphdata = graphdata
        self.pack_start(self._waveform, expand=True, fill=True)
        self.pack_start(self._hscrollbar, expand=False, fill=False)
        self._hscrollbar.connect("value-changed", self.update_model)
        self._graphdata.changed.connect(self.update_scrollbar)

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

if __name__ == '__main__':
    from mock import Mock, Fake
    

    def test_window():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)
        ctrl = Mock({"get_values": [v / 500. for v in xrange(500)],
                     "set_width": None})
        ctrl.changed = Fake()
        waveform = Waveform(ctrl)
        window.add(waveform)
        window.show_all()
        gtk.main()

    def test_rand():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)

        from random import random
        values = [(random() - 0.5) * 2 for i in xrange(500)]        
        ctrl = Mock({"get_values": values, "set_width": None})
        ctrl.changed = Fake()
        waveform = Waveform(ctrl)
        window.add(waveform)
        window.show_all()
        gtk.main()

    def test_sine():
        window = gtk.Window()
        window.resize(500, 200)
        window.connect("delete-event", gtk.main_quit)

        from math import sin
        sine = [sin(2 * 3.14 * 0.01 * x) for x in xrange(500)]
        ctrl = Mock({"get_values": sine, "set_width": None})
        ctrl.changed = Fake()
        waveform = Waveform(ctrl)
        window.add(waveform)
        window.show_all()
        gtk.main()

    test_window()
    test_rand()
    test_sine()
