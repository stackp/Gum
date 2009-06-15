# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import app

# pygtk gets program name from sys.argv[0]. This name appears in
# taskbars when windows are grouped together.
import sys
sys.argv[0] = app.__appname__

from gtkwaveform import GraphView, GraphScrollbar
from gtkfiledialog import FileDialog
import copy
import os.path
import gtk
gtk.gdk.threads_init()

def init():
    """Called when the module is being imported."""
    # Plug callbacks into app.
    app.new_sound_loaded.connect(on_new_sound_loaded)

def main_loop():
    gtk.main()

def on_new_sound_loaded(controller, graph, sel, curs):
    EditorWindow(controller, graph, sel, curs)


class EditorWindow(gtk.Window):

    _windows = []

    def __init__(self, controller, graph, selection, cursor):
        gtk.Window.__init__(self)

        self.ctrl = controller
        
        self.uimanager = self._make_ui_manager()
        accelgroup = self.uimanager.get_accel_group()
        self.add_accel_group(accelgroup)

        self.menubar = self.uimanager.get_widget('/menubar')
        self.toolbar = self.uimanager.get_widget('/toolbar')
        self.toolbar.set_style(gtk.TOOLBAR_ICONS)
        for w in self.toolbar:
            w.set_homogeneous(False)
            w.set_focus_chain([])
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
        
        self.connect("delete-event", self.close)
        self._filename_update()
        self.ctrl.filename_changed.connect(self._filename_update)
        self.ctrl.error.connect(self.display_error)
        icon = self.render_icon(gtk.STOCK_CUT, gtk.ICON_SIZE_MENU)
        self.set_icon(icon)
        self.resize(700, 500)
        self.show_all()
        self._windows.append(self)

    def _make_ui_manager(self):
        ui = '''<ui>
            <menubar name="menubar">
              <menu action="File">
                <menuitem action="New"/>
                <menuitem action="Open"/>
                <menuitem action="Save"/>
                <menuitem action="Save as"/>
                <separator/>
                <menuitem action="Close"/>
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
            <accelerator action="Start"/>
            <accelerator action="End"/>
            <accelerator action="Play"/>
            <accelerator action="Pause"/>
        </ui>'''

        uimanager = gtk.UIManager()
        uimanager.add_ui_from_string(ui)

        # An action is a tuple formed like this:
        # (action_name, stock_id, label, accelerator, tooltip, callback)
        #
        # Actions that are not in a menu (e.g. 'Play') must have an
        # <accelerator> tag in the UI description for the accelerator
        # defined below to be effective.

        actions = [('File', None, '_File'),
                   ('Edit', None, '_Edit'),
                   ('View', None, '_View'),
                   ('Effects', None, '_Effects'),
                   ('Scalpel', None, '_Scalpel'),
                   ('New', gtk.STOCK_NEW, None, None, '', self.new),
                   ('Open', gtk.STOCK_OPEN, None, None, '', self.open),
                   ('Save', gtk.STOCK_SAVE, None, None, '', self.save),
                   ('Save as', gtk.STOCK_SAVE_AS, None, None, '',self.save_as),
                   ('Close', gtk.STOCK_CLOSE, None, None, '', self.close),
                   ('Quit', gtk.STOCK_QUIT, None, None, '', self.quit),
                   ('Play', gtk.STOCK_MEDIA_PLAY, None, 'p', '', self.play),
                   ('Pause', gtk.STOCK_MEDIA_PAUSE, None, 'o', '', self.pause),
                   ('Start', gtk.STOCK_MEDIA_PREVIOUS, None, 'Home', '',
                                                              self.goto_start),
                   ('End', gtk.STOCK_MEDIA_NEXT, None, 'End', '',
                                                                self.goto_end),
                   ('Rewind', gtk.STOCK_MEDIA_REWIND, None, None, '',
                                                                  self.rewind),
                   ('Forward', gtk.STOCK_MEDIA_FORWARD, None, None, '',
                                                                 self.forward),
                   ('Cut', gtk.STOCK_CUT, None, None, '', self.cut),
                   ('Copy', gtk.STOCK_COPY, None, None, '', self.copy),
                   ('Paste', gtk.STOCK_PASTE, None, None, '', self.paste),
                   ('Undo', gtk.STOCK_UNDO, None, '<Ctrl>z', None, self.undo),
                   ('Redo', gtk.STOCK_REDO, None, '<Ctrl><Shift>z', None,
                                                                    self.redo),
                   ('SelectAll', gtk.STOCK_SELECT_ALL, None, '<Ctrl>a', '',
                                                         self.select_all),
                   ('ZoomFit', gtk.STOCK_ZOOM_FIT, None, 'equal', '',
                                                                self.zoom_fit),
                   ('ZoomOut', gtk.STOCK_ZOOM_OUT, None, 'KP_Subtract', '',
                                                                self.zoom_out),
                   ('ZoomIn', gtk.STOCK_ZOOM_IN, None, 'KP_Add', '',
                                                                 self.zoom_in),
                   ('Reverse', None, 'Reverse', None, '', self.reverse),
                   ('Normalize', None, 'Normalize', None, '', self.normalize),
                   ('About', gtk.STOCK_ABOUT, None, None, '', self.about)
                   ]
        actiongroup = gtk.ActionGroup('')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, 0)

        return uimanager

    def _filename_update(self):
        filename = self.ctrl.filename()
        self._update_title(filename)
        self.filedialog.filename = filename

    def _update_title(self, filename=None):
        title = app.__appname__
        if filename:
            title = os.path.basename(filename) + ' - ' + title
        self.set_title(title)

    def display_error(self, title, text):
        d = gtk.MessageDialog(parent=self, buttons=gtk.BUTTONS_CLOSE)
        d.set_title(title)
        d.set_markup(text)
        d.run()
        d.destroy()

    # -- Callbacks

    def __getattr__(self, name):
        """Redirect callbacks to the controller.

        The gtk widget passed to the callback (first argument) will
        not be passed to the controller method.
        
        """
        if name in ["new", "save", "play", "pause", "rewind", "forward",
                    "goto_start", "goto_end", "select_all",
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
        d.set_program_name(app.__appname__)
        d.set_version(app.__version__)
        d.set_website(app.__url__)
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

    def close(self, *args):
        self.ctrl.close()
        self.destroy()
        self._windows.remove(self)

        if not self._windows:
            self.quit()

    def quit(self, *args):
        for win in copy.copy(self._windows):
            win.close()
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
                      "end_selection": None,
                      "selected": True})
    selection.changed = Fake()
    cursor = Mock({'pixel': 20})
    cursor.changed = Fake()
    class FakeController(Fake):
        def __init__(self):
            self.filename_changed = Fake()
            self.error = Fake()
    win = EditorWindow(FakeController(), graph, selection, cursor)
    win.resize(700, 500)
    win.show_all()
    gtk.main()

if __name__ == '__main__':
    test()
else:
    # Module is being imported.
    init()
