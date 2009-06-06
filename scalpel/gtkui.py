# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2008 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import gtk
from gtkwaveform import GraphView, GraphScrollbar
from gtkfiledialog import FileDialog

class MainWindow(gtk.Window):

    def __init__(self, controller, graph, selection, cursor):
        gtk.Window.__init__(self)

        self.ctrl = controller
        
        self.uimanager = self._make_ui_manager()
        self.menubar = self.uimanager.get_widget('/menubar')
        self.toolbar = self.uimanager.get_widget('/toolbar')
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        for w in self.toolbar:
            w.set_homogeneous(False)
        self.waveform = GraphView(graph, selection, cursor)
        self.scrollbar = GraphScrollbar(graph)
        self.statusbar = gtk.Statusbar()
        self.filedialog = FileDialog()

        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.menubar, expand=False, fill=False)
        self.vbox.pack_start(self.toolbar, expand=False, fill=False)
        self.vbox.pack_start(self.waveform, expand=True, fill=True)
        self.vbox.pack_start(self.scrollbar, expand=False, fill=False)
        self.vbox.pack_end(self.statusbar, expand=False, fill=False)
        self.add(self.vbox)
        
        self.connect("delete-event", self.quit)
        self.set_title("scalpel")
        self.resize(700, 500)
        self.show_all()

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
              <menu action="Effects">
                <menuitem action="Reverse"/>
                <menuitem action="Normalize"/>
              </menu>                
              <menu action="Scalpel">
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
                   ('Effects', None, '_Effects'),
                   ('Scalpel', None, '_Scalpel'),
                   ('New', gtk.STOCK_NEW, None, None, '', self.new),
                   ('Open', gtk.STOCK_OPEN, None, None, '',
                                            self.display_exception(self.open)),
                   ('Save', gtk.STOCK_SAVE, None, None, '',
                                            self.display_exception(self.save)),
                   ('Save as', gtk.STOCK_SAVE_AS, None, None, '',
                                         self.display_exception(self.save_as)),
                   ('Quit', gtk.STOCK_QUIT, None, None, '', self.quit),
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
                   ('Reverse', None, 'Reverse', None, '', self.reverse),
                   ('Normalize', None, 'Normalize', None, '', self.normalize),
                   ('About', gtk.STOCK_ABOUT, None, None, '', self.about)
                   ]
        actiongroup = gtk.ActionGroup('')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, 0)

        return uimanager

    def display_exception(self, func):
        """A decorator that display caught exceptions in a window.

        Caught exceptions are reraised.

        """
        def f(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception, e:
                d = gtk.MessageDialog(parent=self, buttons=gtk.BUTTONS_CLOSE)
                d.set_title("Error")
                d.set_markup(str(e))
                d.run()
                d.destroy()
                raise e
        return f

    # -- Callbacks

    def __getattr__(self, name):
        """Redirect callbacks to the controller.

        The gtk widget passed to the callback (first argument) will
        not be passed to the controller method.
        
        """
        if name in ["new", "save", "play", "pause", "rewind", "forward",
                    "goto_start", "goto_end", "select_all", "unselect",
                    "cut", "copy", "paste", "undo", "redo",
                    "zoom_in", "zoom_out", "zoom_fit",
                    "reverse", "normalize"]:
            method = getattr(self.ctrl, name)
            def forward(self, *args):
                method(*args[1:])
            return forward
        else:
            raise AttributeError(name)


    def about(self, *args):
        d = gtk.AboutDialog()
        d.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        d.set_transient_for(self)
        d.set_program_name("Scalpel")
        d.set_version("0.1")
        d.set_copyright("(c) Pierre Duquesne <stackp@online.fr>")
        d.set_comments("A sound editor")
        d.run()
        d.destroy()
        
    def open(self, *args):
        filename = self.filedialog.get_filename(action='open')
        if filename != None:
            self.ctrl.open(filename)

    def save_as(self, *args):
        filename = self.filedialog.get_filename(action='save')
        if filename != None:
            self.ctrl.save_as(filename)

    def quit(self, *args):
        self.ctrl.quit()
        gtk.main_quit()


# -- Tests
           
def test():
    from mock import Fake, Mock
    graph = Mock({"frames_info":(0, 0, [], []),
                  "channels": [[(0, 0.5)]],
                  "set_width": None,
                  "scroll_left": None,
                  "scroll_right": None})
    graph.changed = Fake()
    selection = Mock({"pixels": [50, 100],
                      "start_selection": None,
                      "end_selection": None})
    selection.changed = Fake()
    win = MainWindow(Fake(), graph, selection)
    win.resize(700, 500)
    win.show_all()
    gtk.main()

if __name__ == '__main__':
    test()
