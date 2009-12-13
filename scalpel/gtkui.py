# Scalpel sound editor (http://scalpelsound.online.fr)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

import constants

# pygtk gets program name from sys.argv[0]. This name appears in
# taskbars when windows are grouped together.
import sys
sys.argv[0] = constants.__appname__

import app
import control
from gtkwaveform import GraphView, GraphScrollbar
from gtkfiledialog import FileDialog
import copy
import os.path
import urllib
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

def display_error(title, text, parent=None):
    d = gtk.MessageDialog(parent, buttons=gtk.BUTTONS_CLOSE)
    d.set_title(title)
    d.set_markup(text)
    d.run()
    d.destroy()


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

        # Create and fill the Effects menu
        effect_menu = gtk.Menu()
        for name in app.list_effects():
            item = gtk.MenuItem(label=name)
            item.connect('activate', self.effect, name)
            effect_menu.append(item)
        w = self.uimanager.get_widget('/menubar/Effects')
        w.set_submenu(effect_menu)

        self.waveform = GraphView(graph, selection, cursor)
        self.scrollbar = GraphScrollbar(graph)
        self.statusbar = gtk.Statusbar()
        self.filedialog = FileDialog(app.list_extensions())

        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.menubar, expand=False, fill=False)
        self.vbox.pack_start(self.toolbar, expand=False, fill=False)
        self.vbox.pack_start(self.waveform, expand=True, fill=True)
        self.vbox.pack_start(self.scrollbar, expand=False, fill=False)
        self.vbox.pack_end(self.statusbar, expand=False, fill=False)
        self.add(self.vbox)
        
        # Setup drag and drop
        TARGET_TYPE_TEXT = 80
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                           [("text/uri-list", 0, TARGET_TYPE_TEXT)],
                           gtk.gdk.ACTION_COPY)
        self.connect("drag_data_received", self._open_dropped_files)

        # Keyboard shortcuts
        kval = gtk.gdk.keyval_from_name
        self.handlers = {kval('space'): self.ctrl.toggle_play,
                         kval('ISO_Level3_Shift'): self.ctrl.play}
        self.connect('key_press_event', self.on_key_press_event)

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
                <menuitem action="Save Selection as"/>
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
                <menuitem action="Mix"/>
                <separator/>
                <menuitem action="SelectAll"/>
              </menu>
              <menu action="View">
                <menuitem action="ZoomIn"/>
                <menuitem action="ZoomOut"/>
                <menuitem action="ZoomFit"/>
              </menu>
              <menu action="Effects">
              </menu>                
              <menu action="Scalpel">
                <menuitem action="About"/>
              </menu>
            </menubar>
            <toolbar name="toolbar">
              <toolitem action="Open"/>
              <separator/>
              <toolitem action="ZoomFit"/>
              <toolitem action="ZoomOut"/>
              <toolitem action="ZoomIn"/>
              <separator/>
              <toolitem action="Start"/>
              <toolitem action="Stop"/>
              <toolitem action="Play"/>
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
            <accelerator action="Stop"/>
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
                   ('Effects', None, 'Effe_cts'),
                   ('Scalpel', None, '_Scalpel'),
                   ('New', gtk.STOCK_NEW, None, None, '', self.new),
                   ('Open', gtk.STOCK_OPEN, None, None, '', self.open),
                   ('Save', gtk.STOCK_SAVE, None, None, '', self.save),
                   ('Save as', gtk.STOCK_SAVE_AS, None, None, '',self.save_as),
                   ('Save Selection as', gtk.STOCK_SAVE_AS,'Save Selection As',
                                 '<Ctrl><Alt>s', None, self.save_selection_as),
                   ('Close', gtk.STOCK_CLOSE, None, None, '', self.close),
                   ('Quit', gtk.STOCK_QUIT, None, None, '', self.quit),
                   ('Play', gtk.STOCK_MEDIA_PLAY, None, 'p', '', self.play),
                   ('Stop', gtk.STOCK_MEDIA_STOP, None, 'o', '', self.stop),
                   ('Start', gtk.STOCK_MEDIA_PREVIOUS, None, 'Home', '',
                                                              self.goto_start),
                   ('End', gtk.STOCK_MEDIA_NEXT, None, 'End', '',
                                                                self.goto_end),
                   ('Cut', gtk.STOCK_CUT, None, None, '', self.cut),
                   ('Copy', gtk.STOCK_COPY, None, None, '', self.copy),
                   ('Paste', gtk.STOCK_PASTE, None, None, '', self.paste),
                   ('Mix', gtk.STOCK_ADD, 'Mix', '<Ctrl><Shift>v', None,
                                                                     self.mix),
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
                   ('About', gtk.STOCK_ABOUT, None, None, '', self.about)
                   ]
        actiongroup = gtk.ActionGroup('')
        actiongroup.add_actions(actions)
        uimanager.insert_action_group(actiongroup, 0)

        return uimanager

    def _close(self):
        try:
            self.ctrl.close()
        except control.FileNotSaved:
            proceed = self._show_dialog_close()
            if not proceed:
                return False
            self.ctrl.close(force=True)

        self.destroy()
        self._windows.remove(self)

        if not self._windows:
            self.quit()

        return True

    def _show_dialog_close(self):
        dialog = gtk.MessageDialog(parent=self, type=gtk.MESSAGE_WARNING)
        name = self.ctrl.filename() or "sound"
        name = os.path.basename(name)
        name = name.replace('&', '&amp;')
        dialog.set_markup("<b>Save %s before closing?</b>" % name)
        dialog.add_button("Close _without saving", gtk.RESPONSE_NO)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.add_button(gtk.STOCK_SAVE_AS, gtk.RESPONSE_YES)
        response = dialog.run()
        dialog.destroy()
        proceed = False
        if response == gtk.RESPONSE_NO:
            proceed = True
        elif response == gtk.RESPONSE_YES:
            saved = self.save_as()
            if saved:
                proceed = True
        return proceed

    def _filename_update(self):
        filename = self.ctrl.filename()
        self._update_title(filename)
        self.filedialog.filename = filename

    def _update_title(self, filename=None):
        title = constants.__appname__
        if filename:
            title = os.path.basename(filename) + ' - ' + title
        self.set_title(title)

    def _open_dropped_files(self, widget, context, x, y,
                            selection, targetType, time):
        """Open files dragged and dropped on the window."""
        filenames = selection.data.split()
        prefix = 'file://'
        for filename in filenames:
            # Extract the actual filename
            if filename.startswith(prefix):
                filename = filename[len(prefix):]
            filename = urllib.unquote(filename)
            self._do_open(filename)

    def display_error(self, title, text):
        display_error(title, text, parent=self)

    def busy(method):
        """A decorator to show a "busy" mouse cursor."""
        def decorated(self, *args):
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            while gtk.events_pending():
                gtk.main_iteration(False)
            try:
                method(self, *args)
            finally:
                self.window.set_cursor(None)
        return decorated

    @busy
    def _do_open(self, filename):
        self.ctrl.open(filename)

    # -- GTK Callbacks

    def __getattr__(self, name):
        """Redirect callbacks to the controller.

        The gtk widget passed to the callback (first argument) will
        not be passed to the controller method.
        
        """
        if name in ["new", "save", "play", "stop",
                    "goto_start", "goto_end", "select_all",
                    "cut", "copy", "paste", "mix", "undo", "redo",
                    "zoom_in", "zoom_out", "zoom_fit"]:
            method = getattr(self.ctrl, name)
            def forward(self, *args):
                method(*args[1:])
            return forward
        else:
            raise AttributeError(name)

    def on_key_press_event(self, widget, event):
        if event.keyval in self.handlers:
            handler = self.handlers[event.keyval]
            handler()
    
    @busy
    def effect(self, widget, *args):
        self.ctrl.effect(*args)

    def about(self, *args):
        d = gtk.AboutDialog()
        d.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        d.set_transient_for(self)
        d.set_program_name(constants.__appname__)
        d.set_version(constants.__version__)
        d.set_website(constants.__url__)
        d.set_copyright("(c) Pierre Duquesne <stackp@online.fr>")
        d.set_comments("A sound editor")
        d.run()
        d.destroy()

    def open(self, *args):
        filename = self.filedialog.get_filename(action='open')
        if filename != None:
            self._do_open(filename)

    def save_as(self, *args):
        filename = self.filedialog.get_filename(action='save')
        saved = False
        if filename != None:
            self.ctrl.save_as(filename)
            saved = True
        return saved

    def save_selection_as(self, *args):
        # FIXME: title
        filename = self.filedialog.get_filename(action='save')
        if filename != None:
            self.ctrl.save_selection_as(filename)

    def close(self, *args):
        self._close()
        # Tell GTK not to hide the window, we take care of that:
        return True

    def quit(self, *args):
        for win in copy.copy(self._windows):
            if not win._close():
                return
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

    display_error("Title", "Text")

if __name__ == '__main__':
    test()
else:
    # Module is being imported.
    init()
