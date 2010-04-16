import effect
import gtk

class AbortException(Exception):
    pass


class VolumeDialog(gtk.Dialog):

    volume = 100

    def __init__(self, parent):
        gtk.Dialog.__init__(self, title="Volume",
                   flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                   buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_APPLY, gtk.RESPONSE_ACCEPT))
        self.set_default_response(gtk.RESPONSE_ACCEPT)
        self.set_transient_for(parent)

        self.adjustment = gtk.Adjustment(self.__class__.volume, 0, 200, 1)
        scale = gtk.HScale(self.adjustment)
        scale.set_draw_value(False)
        spin = gtk.SpinButton(self.adjustment, climb_rate=1, digits=0)
        label = gtk.Label("%")

        hbox = gtk.HBox()
        hbox.set_border_width(5)
        hbox.pack_start(scale, True, True)
        hbox.pack_start(spin, False, False)
        hbox.pack_end(label, False, False)
        self.vbox.pack_start(hbox, expand=True, fill=True, padding=10)

    def get_volume(self):
        self.show_all()
        response = self.run()
        self.hide()
        if response != gtk.RESPONSE_ACCEPT:
            raise AbortException
        self.__class__.volume = self.adjustment.get_value()
        return self.__class__.volume


def volume(sound, start, end):

    def process(volume):
        gain = volume / 100.
        x = sound.frames[start:end]
        y = x * gain
        sound.paste(start, end, y)
        
    def ui(parent):
        dialog = VolumeDialog(parent)
        try:
            volume = dialog.get_volume()
        except AbortException:
            return
        else:
            process(volume)
    
    return ui


effect.effects['Volume'] = volume
