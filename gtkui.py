import gtk
from gtkwaveform import SelectableWaveform, GraphScrollbar


class MainWindow(gtk.Window):

    def __init__(self, ui_controller, wf_controller, selection):
        gtk.Window.__init__(self)

        self.ctrl = ui_controller
        
        self.uimanager = self._make_ui_manager()
        self.menubar = self.uimanager.get_widget('/menubar')
        self.toolbar = self.uimanager.get_widget('/toolbar')
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        for w in self.toolbar:
            w.set_homogeneous(False)
        self.waveform = SelectableWaveform(wf_controller, selection)
        self.scrollbar = GraphScrollbar(wf_controller)
        self.statusbar = gtk.Statusbar()

        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.menubar, expand=False, fill=False)
        self.vbox.pack_start(self.toolbar, expand=False, fill=False)
        self.vbox.pack_start(self.waveform, expand=True, fill=True)
        self.vbox.pack_start(self.scrollbar, expand=False, fill=False)
        self.vbox.pack_end(self.statusbar, expand=False, fill=False)
        self.add(self.vbox)
        
        self.connect("delete-event", gtk.main_quit)
        self.set_title("scalpel")

    def _make_ui_manager(self):
        ui = '''<ui>
            <menubar name="menubar">
              <menu action="File">
                <menuitem action="New"/>
                <menuitem action="Open"/>
                <menuitem action="Save"/>
                <menuitem action="Save as"/>
                <separator/>
                <menuitem action="Quit"/>
              </menu>
              <menu action="Edit">
                <menuitem action="Undo"/>
                <menuitem action="Redo"/>
                <separator/>
                <menuitem action="Cut"/>
                <menuitem action="Copy"/>
                <menuitem action="Paste"/>
                <separator/>
                <menuitem action="SelectAll"/>
                <menuitem action="Unselect"/>
              </menu>
              <menu action="View">
                <menuitem action="ZoomIn"/>
                <menuitem action="ZoomOut"/>
                <menuitem action="ZoomFit"/>
              </menu>
              <menu action="Help">
                <menuitem action="About"/>
              </menu>
            </menubar>
            <toolbar name="toolbar">
              <toolitem action="Open"/>
              <toolitem action="Save"/>
              <separator/>
              <toolitem action="ZoomFit"/>
              <toolitem action="ZoomOut"/>
              <toolitem action="ZoomIn"/>
              <separator/>
              <toolitem action="Start"/>
              <toolitem action="Rewind"/>
              <toolitem action="Pause"/>
              <toolitem action="Play"/>
              <toolitem action="Forward"/>
              <toolitem action="End"/>
              <separator/>
              <toolitem action="Cut"/>
              <toolitem action="Copy"/>
              <toolitem action="Paste"/>
              <separator/>
              <toolitem action="Undo"/>
              <toolitem action="Redo"/>
            </toolbar>
        </ui>'''

        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(ui)

        # An action is a tuple formed like this:
        # (action_name, stock_id, label, accelerator, tooltip, callback)

        actions = [('File', None, '_File'),
                   ('Edit', None, '_Edit'),
                   ('View', None, '_View'),
                   ('Help', None, '_Help'),
                   ('New', gtk.STOCK_NEW, None, None, '', self.new),
                   ('Open', gtk.STOCK_OPEN, None, None, '', self.open),
                   ('Save', gtk.STOCK_SAVE, None, None, '', self.save),
                   ('Save as', gtk.STOCK_SAVE_AS, None, None, '',self.save_as),
                   ('Quit', gtk.STOCK_QUIT, None, None, '', gtk.main_quit),
                   ('Play', gtk.STOCK_MEDIA_PLAY, None, None, '', self.play),
                   ('Pause', gtk.STOCK_MEDIA_PAUSE, None, None, '',self.pause),
                   ('Start', gtk.STOCK_MEDIA_PREVIOUS, None, None, '',
                                                              self.goto_start),
                   ('End', gtk.STOCK_MEDIA_NEXT, None, None, '',self.goto_end),
                   ('Rewind', gtk.STOCK_MEDIA_REWIND, None, None, '',
                                                                  self.rewind),
                   ('Forward', gtk.STOCK_MEDIA_FORWARD, None, None, '',
                                                                 self.forward),
                   ('Cut', gtk.STOCK_CUT, None, None, '', self.cut),
                   ('Copy', gtk.STOCK_COPY, None, None, '', self.copy),
                   ('Paste', gtk.STOCK_PASTE, None, None, '', self.paste),
                   ('Undo', gtk.STOCK_UNDO, None, None, '', self.undo),
                   ('Redo', gtk.STOCK_REDO, None, None, '', self.redo),
                   ('SelectAll', gtk.STOCK_SELECT_ALL, None, None, '',
                                                         self.select_all),
                   ('Unselect', None, 'Unselect', None, '', self.unselect),
                   ('ZoomFit', gtk.STOCK_ZOOM_FIT, None, None, '',
                                                                self.zoom_fit),
                   ('ZoomOut', gtk.STOCK_ZOOM_OUT, None, None, '',
                                                                self.zoom_out),
                   ('ZoomIn', gtk.STOCK_ZOOM_IN, None, None, '', self.zoom_in),
                   ('About', gtk.STOCK_ABOUT, None, None, '', self.about)
                   ]
        actiongroup = gtk.ActionGroup('')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, 0)

        return uimanager

    # -- Callbacks

    def __getattr__(self, name):
        """Redirect callbacks to the controller.

        The gtk widget passed to the callback (first argument) will
        not be passed to the controller method.
        
        """
        if name in ["new", "save", "play", "pause", "rewind", "forward",
                    "goto_start", "goto_end", "select_all", "unselect",
                    "cut", "copy", "paste", "undo", "redo",
                    "zoom_in", "zoom_out", "zoom_fit"]:
            method = getattr(self.ctrl, name)
            def forward(self, *args):
                method(*args[1:])
            return forward
        else:
            raise AttributeError(name)


    def about(self, *args):
        d = gtk.Dialog(title="About",
                       flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                       buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_OK))
        d.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        d.set_transient_for(self)
        d.vbox.add(gtk.Label("Scalpel"))
        d.show_all()
        d.run()
        d.destroy()
        
    def open(self, *args):
        chooser = gtk.FileChooserDialog(action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        response = chooser.run()
        filename = chooser.get_filename()
        chooser.destroy()
        if response == gtk.RESPONSE_OK:
            self.ctrl.open(filename)

    def save_as(self, *args):
        pass

# -- Tests
           
def test():
    from mock import Fake, Mock
    wf_ctrl = Mock({"get_info": (0, 0, [], [])})
    win = MainWindow(Fake(), wf_ctrl)
    win.resize(700, 500)
    win.show_all()
    gtk.main()

if __name__ == '__main__':
    test()
