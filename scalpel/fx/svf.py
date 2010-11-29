from effect import effects
import numpy
import gtk
import functools

svf_index = {"High Pass": 0, "Band Pass": 1, "Low Pass": 2}

def svf(x, f, damping, samplerate):
    """State variable filters. DAFX book, Section 2.2, page 36."""
    F = 2 * numpy.sin(numpy.pi * f / samplerate)
    Q = 2 * damping

    yh = numpy.zeros(len(x))
    yb = numpy.zeros(len(x))
    yl = numpy.zeros(len(x))
    for n in range(len(x)):
        yh[n] = x[n] - yl[n-1] - Q * yb[n-1]
        yb[n] = F * yh[n] + yb[n-1]
        yl[n] = F * yb[n] + yl[n-1]
    return yh, yb, yl

try:
    from _svf import svf
except ImportError:
    print ("Warning: Optimized implementation of state variable filters not "
           "found, using pure python implementation instead.")


class SVFDialog(gtk.Dialog):
    def __init__(self, title):
        gtk.Dialog.__init__(self, title + " State Variable Filter", 
                   flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT))

        table = gtk.Table(3, 2)
        self.frequency = gtk.Adjustment(500, 0, 5000, 1)
        self.damping = gtk.Adjustment(0.5, 0.01, 3, 0.1)

        for i, text in enumerate(["Frequency :", "Damping :"]):
            align = gtk.Alignment(1, 0.5, 0, 0)
            label = gtk.Label(text)
            align.add(label)
            table.attach(align, 0, 1, i, i + 1, xoptions=0)

        for i, adj in enumerate([self.frequency, self.damping]):
            scale = gtk.HScale(adj)
            scale.set_draw_value(False)
            table.attach(scale, 1, 2, i, i + 1, xoptions=gtk.EXPAND|gtk.FILL)

        fspin = gtk.SpinButton(self.frequency, climb_rate=1, digits=2)
        dspin = gtk.SpinButton(self.damping, climb_rate=1, digits=2)
        for i, spin in enumerate([fspin, dspin]):
            align = gtk.Alignment(0, 0.5, 0, 0)
            align.add(spin)
            table.attach(align, 2, 3, i, i + 1, xoptions=0)
        
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        table.set_border_width(5)
        self.vbox.pack_start(table, expand=False, fill=False)
        self.resize(500, 1)

    def get_parameters(self):
        self.show_all()
        response = self.run()
        self.hide()
        if response != gtk.RESPONSE_ACCEPT:
            raise effect.AbortException
        freq = self.frequency.get_value()
        damp = self.damping.get_value()
        return freq, damp


def process_each_channel(func, x):
    ndim = x.ndim
    if ndim == 1:
        x = [x]
    else:
        x = x.transpose()
    y = []
    for channel in x:
        y.append(func(channel))
    if ndim == 1:
        y = y[0]
    else:
        y = numpy.array(y).transpose()
    return y


def svf_fx(type, sound, start, end):

    def process(freq, damp):
        def apply(channel):
            filtered = svf(channel, freq, damp, sound.samplerate)
            i = svf_index[type]
            return filtered[i]
        y = process_each_channel(apply, sound.frames[start:end])
        sound.paste(start, end, y)

    def ui(parent):
        d = SVFDialog(type)
        d.set_transient_for(parent)
        try:
            freq, damp = d.get_parameters()
        except:
            return
        process(freq, damp)

    return ui


effects['Filter: High Pass'] = functools.partial(svf_fx, "High Pass")
effects['Filter: Band Pass'] = functools.partial(svf_fx, "Band Pass")
effects['Filter: Low Pass'] = functools.partial(svf_fx, "Low Pass")
