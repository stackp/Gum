import gtk

class EffectDialog(gtk.Dialog):
    def __init__(self, title=""):
        gtk.Dialog.__init__(self, title,
                   flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT))

        self.parameters = {}
        self.set_decorated(False)
        self.resize(400, 1)
        self.set_icon(self.render_icon(gtk.STOCK_CUT, gtk.ICON_SIZE_DIALOG))
        self.table = gtk.Table(3, 2)
        self.table.set_col_spacings(10)
        self.table.set_row_spacings(10)
        self.table.set_border_width(20)
        self.vbox.pack_start(self.table, expand=False, fill=False)

    def add_slider(self, name, value=5, lower=0, upper=10, ndigits=0):

        adj = gtk.Adjustment(value, lower, upper)
        self.parameters[name] = adj

        vposition = len(self.parameters) - 1

        label = gtk.Label(name + " :")
        align = gtk.Alignment(1, 1, 0, 0)
        align.add(label)
        self.table.attach(align, 0, 1, vposition, vposition + 1,
                          xoptions=gtk.FILL)

        scale = gtk.HScale(adj)
        scale.set_digits(ndigits)
        scale.set_draw_value(True)
        scale.set_restrict_to_fill_level(True)
        self.table.attach(scale, 1, 2, vposition, vposition + 1,
                          xoptions=gtk.EXPAND|gtk.FILL)

    def proceed(self):
        self.show_all()
        response = self.run()
        self.hide()
        if response != gtk.RESPONSE_ACCEPT:
            return
        values = {}
        for name in self.parameters:
            adj = self.parameters[name]
            values[name] = adj.get_value()
        self.callback(values)

    def callback(self, parameters):
        """Reaffect this attribute with a method that will apply the effect."""
        print parameters


if __name__ == '__main__':
    d = EffectDialog('Effect')
    d.add_slider("Delay", 500, 0, 5000)
    d.add_slider("Feedback", 50, 0, 99)
    d.proceed()
