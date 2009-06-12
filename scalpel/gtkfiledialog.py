import gtk

class FileDialog(object):
    """Handle a pair of file dialogs (open and save)."""

    def __init__(self):
        self.filename = None

    def get_filename(self, action='open'):
        """Run a dialog and return a filename or None.

        Valid actions are 'open' and 'save'.

        """
        # I used to create the dialogs only once (on object
        # initialization), and hide and show them, but I can not
        # manage to pre-select a filename after a dialog have been
        # used once. I guess file chooser dialogs are just throwaway
        # objects. Thus, recreate them every time.
        if action == 'open':
            chooser = gtk.FileChooserDialog(
                                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
            title = 'Open file:'
            stock = gtk.STOCK_OPEN

        elif action == 'save':
            chooser = gtk.FileChooserDialog(
                                action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_SAVE, gtk.RESPONSE_OK))
            title = 'Save as:'
            stock = gtk.STOCK_SAVE

        else:
            raise Exception("action must be 'open' or 'save' (got '%s')"
                            % action)

        chooser.set_title(title)
        icon = chooser.render_icon(stock, gtk.ICON_SIZE_MENU)
        chooser.set_icon(icon)
        if self.filename:
            chooser.select_filename(self.filename)
        response = chooser.run()
        filename = chooser.get_filename()
        chooser.destroy()

        # By default, the GTK loop would wait until the process is
        # idle to process events. Now, it is very probable that file
        # I/O will be performed right after this method call and that
        # would delay hiding the dialog until I/O are done. So,
        # process pending events to hide the dialog right now.
        while gtk.events_pending():
            gtk.main_iteration(False)

        if response == gtk.RESPONSE_OK:
            return filename
        else:
            return None


def test():
    d = FileDialog()
    print d.get_filename(action='open')
    print d.get_filename(action='save')
    try:
        d.get_filename(action='nonsense')
    except Exception, e:
        print e
    else:
        assert False

if __name__ == '__main__':
    test()
