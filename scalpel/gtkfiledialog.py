import gtk

class FileDialog(object):
    """Handle a pair of file dialogs (open and save)."""

    title = ""
    icon = None
    title = 'Open file:'
    stock = gtk.STOCK_OPEN
    action = gtk.FILE_CHOOSER_ACTION_OPEN
    buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

    def __init__(self, extensions=[], parent=None, filename=None):
        self.filename = filename
        self.extensions = extensions
        self.chooser = gtk.FileChooserDialog(parent=parent,
                                             action=self.action,
                                             buttons=self.buttons)
        self.chooser.set_title(self.title)
        icon = self.chooser.render_icon(self.stock, gtk.ICON_SIZE_MENU)
        self.chooser.set_icon(icon)
        if self.filename:
            self.chooser.select_filename(self.filename)

        # Supported files filter
        filter = gtk.FileFilter()
        filter.set_name("Supported files")
        for ext in self.extensions:
            filter.add_pattern("*." + ext)
        self.chooser.add_filter(filter)
        self.chooser.set_filter(filter)

        # All files filter
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        self.chooser.add_filter(filter)

    def get_filename(self):
        response = self.chooser.run()
        filename = self.chooser.get_filename()
        self.hide_dialog()
        if response == gtk.RESPONSE_OK:
            return filename
        else:
            return None

    def hide_dialog(self):
        self.chooser.destroy()
        # By default, the GTK loop waits until the process is idle to
        # process events. Now, it is very probable that file I/O will
        # be performed right after this method was called and that
        # would delay hiding the dialog until I/O are done. So,
        # process pending events to hide the dialog right now.
        while gtk.events_pending():
            gtk.main_iteration(False)


class OpenFileDialog(FileDialog):

    title = 'Open file:'
    stock = gtk.STOCK_OPEN
    action = gtk.FILE_CHOOSER_ACTION_OPEN
    buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
               gtk.STOCK_OPEN, gtk.RESPONSE_OK)

    def get_filenames(self):
        self.chooser.set_select_multiple(True)
        response = self.chooser.run()
        filenames = self.chooser.get_filenames()
        self.hide_dialog()
        if response == gtk.RESPONSE_OK:
            return filenames
        else:
            return []

class SaveFileDialog(FileDialog):

    title = 'Save as:'
    stock = gtk.STOCK_SAVE
    action = gtk.FILE_CHOOSER_ACTION_SAVE
    buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
               gtk.STOCK_SAVE, gtk.RESPONSE_OK)


class SaveSelectionFileDialog(SaveFileDialog):

    title = 'Save selection as:'


def test():
    d = FileDialog()
    print d.get_filename()

    d = OpenFileDialog()
    print d.get_filename()

    d = SaveFileDialog()
    print d.get_filename()

if __name__ == '__main__':
    test()
