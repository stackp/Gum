import gtk
import os

class FileDialog(object):
    """Handle a pair of file dialogs (open and save).

    Useful to keep the current directory sync'ed between both
    dialogs. Eliminates redundant code too.

    """
    def __init__(self):
        self.curdir = os.curdir
        self.open_dialog = gtk.FileChooserDialog(
                                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        self.save_dialog = gtk.FileChooserDialog(
                                action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_SAVE, gtk.RESPONSE_OK))

    def get_filename(self, action='open'):
        """Run a dialog and return a filename or None.

        Valid actions are 'open' and 'save'.

        """
        if action == 'open':
            chooser = self.open_dialog
        elif action == 'save':
            chooser = self.save_dialog
        else:
            raise Exception("action must be 'open' or 'save' (got '%s')"
                            % action)

        chooser.set_current_folder(self.curdir)
        response = chooser.run()
        filename = chooser.get_filename()
        chooser.hide()

        # By default, the GTK loop would wait until the process is
        # idle to process events. Now, it is very probable that file
        # I/O will be performed right after this method call and that
        # would delay hiding the dialog until I/O are done. So,
        # process pending events to hide the dialog right now.
        while gtk.events_pending():
            gtk.main_iteration(False)

        if response == gtk.RESPONSE_OK:
            self.curdir = os.path.dirname(filename)
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
