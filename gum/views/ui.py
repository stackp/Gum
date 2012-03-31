# Gum sound editor (https://github.com/stackp/Gum)
# Copyright 2009 (C) Pierre Duquesne <stackp@online.fr>
# Licensed under the Revised BSD License.

from gum import constants

# pygtk gets program name from sys.argv[0]. This name appears in
# taskbars when windows are grouped together.
import sys
sys.argv[0] = constants.__appname__

from gum import app
from gum.controllers import Editor, editor
from waveform import GraphView, GraphScrollbar
from filedialog import OpenFileDialog, SaveFileDialog, SaveSelectionFileDialog
import copy
import os.path
import urllib
import gobject
import gtk
gtk.gdk.threads_init()

def init():
    """Called when the module is being imported."""
    notebook = EditorNotebook()
    win = EditorWindow(notebook)
    # Plug callbacks into app.
    app.new_sound_loaded.connect(win.on_new_sound_loaded)

def main_loop():
    gtk.main()

def display_error(title, text, parent=None):
    d = gtk.MessageDialog(parent, type=gtk.MESSAGE_ERROR,
                          buttons=gtk.BUTTONS_CLOSE)
    d.set_icon(d.render_icon(gtk.STOCK_CUT, gtk.ICON_SIZE_DIALOG))
    d.set_title(title)
    d.set_markup(text)
    d.run()
    d.destroy()

class EditorWindow(gtk.Window):

    def __init__(self, notebook):
        gtk.Window.__init__(self)

        self.notebook = notebook
        self.notebook.root_window = self
        self.notebook.connect('filename-changed', self._on_filename_changed)
        self.notebook.connect('error', self.display_error)

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

        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.menubar, expand=False, fill=False)
        self.vbox.pack_start(self.toolbar, expand=False, fill=False)
        self.vbox.pack_start(self.notebook, expand=True, fill=True)
        self.add(self.vbox)
        
        # Setup drag and drop
        TARGET_TYPE_TEXT = 80
        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                           [("text/uri-list", 0, TARGET_TYPE_TEXT)],
                           gtk.gdk.ACTION_COPY)
        self.connect("drag_data_received", self._open_dropped_files)

        # Keyboard shortcuts
        kval = gtk.gdk.keyval_from_name
        self.handlers = {'space': self.toggle_play,
                         'ISO_Level3_Shift': self.play,
                         '<Shift>Home': self.select_till_start,
                         '<Shift>End': self.select_till_end}

        self.connect('key_press_event', self.on_key_press_event)

        self.connect("delete-event", self.quit)
        self.set_icon(self.render_icon(gtk.STOCK_CUT, gtk.ICON_SIZE_DIALOG))
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
              <menu action="Gum">
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
                   ('Gum', None, '_Gum'),
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

    def on_new_sound_loaded(self, editor, graph, sel, curs):
        page = EditorPage(editor, graph, sel, curs)
        self.notebook.add_page(page)

    def _on_filename_changed(self, notebook, filename):
        self._filename_update(filename)

    def _filename_update(self, filename):
        self._update_title(filename)

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

    def display_error(self, widget, title, text):
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
        self.notebook.open(filename)

    # -- GTK Callbacks

    def __getattr__(self, name):
        """Redirect callbacks.

        The gtk widget passed to the callback (first argument) will
        not be passed to the invoked method.

        """
        if name in ["new", "save", "play", "toggle_play", "stop",
                    "goto_start", "goto_end", "select_all",
                    "cut", "copy", "paste", "mix", "undo", "redo",
                    "zoom_in", "zoom_out", "zoom_fit",
                    "select_till_start", "select_till_end"]:
            method = getattr(self.notebook, name)
            def forward(*args):
                method(*args[1:])
            return forward
        else:
            raise AttributeError(name)

    def on_key_press_event(self, widget, event):
        key = gtk.gdk.keyval_name(event.keyval)
        if event.state is gtk.gdk.SHIFT_MASK:
            key = '<Shift>' + key
        if key in self.handlers:
            handler = self.handlers[key]
            handler()

    @busy
    def effect(self, widget, *args):
        dialog = self.notebook.effect(*args)
        if dialog:
            dialog.set_transient_for(self)
            dialog.proceed()

    def about(self, *args):
        d = gtk.AboutDialog()
        d.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        d.set_transient_for(self)
        d.set_program_name(constants.__appname__)
        d.set_version(constants.__version__)
        d.set_website(constants.__url__)
        d.set_copyright("(c) Pierre Duquesne <stackp@online.fr>")
        d.set_comments("An audio editor")
        d.run()
        d.destroy()

    def open(self, *args):
        dialog = OpenFileDialog(app.list_extensions(), parent=self,
                                filename=self.notebook.filename())
        filenames = dialog.get_filenames()
        for filename in filenames:
            self._do_open(filename)

    def save_as(self, *args):
        dialog = SaveFileDialog(app.list_extensions(), parent=self,
                                filename=self.notebook.filename())
        filename = dialog.get_filename()
        saved = False
        if filename != None:
            self.notebook.save_as(filename)
            saved = True
        return saved

    def save_selection_as(self, *args):
        dialog = SaveSelectionFileDialog(app.list_extensions(), parent=self,
                                         filename=self.notebook.filename())
        filename = dialog.get_filename()
        if filename != None:
            self.notebook.save_selection_as(filename)

    def close(self, *args):
        closed = self.notebook.close_page()
        if self.notebook.is_empty():
            self.quit()
        return closed

    def quit(self, *args):
        while not self.notebook.is_empty():
            if not self.close():
                # Tell GTK not to hide the window:
                return True
        gtk.main_quit()


class EditorNotebook(gtk.Notebook):

    __gsignals__ = {'filename-changed': (gobject.SIGNAL_RUN_LAST,
                                         gobject.TYPE_NONE,
                                         (gobject.TYPE_PYOBJECT,)),
                    'error': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                              (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT))}

    def __init__(self):
        gtk.Notebook.__init__(self)
        self.root_window = None
        self.set_scrollable(True)
        self.set_show_border(False)
        self.popup_enable()
        self.connect("switch-page", self.on_page_switch)
        self.connect("page-added", self.hide_show_tabs)
        self.connect("page-removed", self.hide_show_tabs)

    def on_page_switch(self, notebook, _, numpage):
        page = self.get_nth_page(numpage)
        self.emit("filename-changed", page.filename())

    def on_filename_changed(self, widget, filename):
        current_page = self.get_nth_page(self.get_current_page())
        if widget is current_page:
            self.emit("filename-changed", filename)

    def on_error(self, widget, title, text):
        self.emit('error', title, text)

    def hide_show_tabs(self, *args):
        if self.get_n_pages() <= 1:
            self.set_property('show-tabs', False)
        else:
            self.set_property('show-tabs', True)

    def add_page(self, page):
        page.show_all()
        i = self.append_page_menu(page, tab_label=page.tab,
                                  menu_label=page.menu_title)
        self.set_tab_reorderable(page, True)
        self.set_current_page(i)
        page.connect("filename-changed", self.on_filename_changed)
        page.connect('must-close', self.close_page_by_id)
        page.connect('error', self.on_error)
        self.emit("filename-changed", page.filename())

    def is_empty(self):
        return self.get_n_pages() == 0

    def close_page_by_id(self, widget):
        for numpage in range(self.get_n_pages()):
            page = self.get_nth_page(numpage)
            if page is widget:
                return self.close_page(numpage)

    def close_page(self, numpage=None):
        if numpage is None:
            numpage = self.get_current_page()
        try:
            self._close_page(numpage, force=False)
        except editor.FileNotSaved:
            page = self.get_nth_page(numpage)
            name = page.filename() or "sound"
            proceed = self._show_dialog_close(name)
            if not proceed:
                return False
            else:
                self._close_page(numpage, force=True)
        return True

    def _close_page(self, numpage, force=False):
        page = self.get_nth_page(numpage)
        page.close(force)
        self.remove_page(numpage)
        page.destroy()
        return True

    def _show_dialog_close(self, name):
        dialog = gtk.MessageDialog(parent=self.root_window,
                                   type=gtk.MESSAGE_WARNING)
        name = os.path.basename(name)
        name = name.replace('&', '&amp;')
        dialog.set_markup("<b>Save %s before closing?</b>" % name)
        dialog.add_button("Close _without saving", gtk.RESPONSE_NO)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_YES)
        dialog.set_default_response(gtk.RESPONSE_CANCEL)
        response = dialog.run()
        dialog.destroy()
        proceed = False
        if response == gtk.RESPONSE_NO:
            proceed = True
        elif response == gtk.RESPONSE_YES:
            self.save()
            proceed = True
        return proceed

    def __getattr__(self, name):
        if name in ["new", "save", "play", "toggle_play", "stop",
                    "goto_start", "goto_end", "select_all",
                    "cut", "copy", "paste", "mix", "undo", "redo",
                    "zoom_in", "zoom_out", "zoom_fit",
                    "select_till_start", "select_till_end",
                    "effect", "open", "save_as", "save_selection_as",
                    "filename"]:
            def forward(*args):
                page = self.get_nth_page(self.get_current_page())
                method = getattr(page, name)
                return method(*args)
            return forward
        else:
            raise AttributeError(name)


class EditorPage(gtk.VBox):

    __gsignals__ = {'filename-changed': (gobject.SIGNAL_RUN_LAST,
                                        gobject.TYPE_NONE,
                                         (gobject.TYPE_PYOBJECT,)),
                    'must-close': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                                   ()),
                    'error': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                              (gobject.TYPE_PYOBJECT,gobject.TYPE_PYOBJECT))}

    def __init__(self, editor, graph, selection, cursor):
        gtk.VBox.__init__(self)
        self.ctrl = editor

        # Close button
        image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.set_focus_on_click(False)
        button.set_image(image)
        style = gtk.RcStyle()
        style.xthickness = 0
        style.ythickness = 0
        button.modify_style(style)
        button.connect("clicked", self.must_close)

        # Tab title
        self.title = gtk.Label()
        self.tab = gtk.HBox()
        self.tab.modify_style(style)
        self.tab.pack_start(self.title, True, True)
        self.tab.pack_end(button, False, False)
        self.tab.show_all()

        # Popup menu page title
        self.menu_title = gtk.Label()

        self.waveform = GraphView(graph, selection, cursor)
        self.scrollbar = GraphScrollbar(graph)
        self.statusbar = gtk.Statusbar()
        self.pack_start(self.waveform, expand=True, fill=True)
        self.pack_start(self.scrollbar, expand=False, fill=False)
        self.pack_end(self.statusbar, expand=False, fill=False)
        self.waveform.connect("selection-changed",
                                              self.on_selection_changed)
        self.ctrl.filename_changed.connect(self._update_filename)
        self.ctrl.error.connect(self.emit_error)
        self.connect("destroy", self.on_destroy)
        self._update_filename()

    def must_close(self, *args):
        self.emit('must-close')

    def close(self, force=False):
        self.ctrl.close(force)

    def on_destroy(self, widget):
        # For some reason, the "tab" widget has to be destroyed
        # explicitely. Otherwise, it does not get garbage-collected.
        self.tab.destroy()

    def emit_error(self, title, text):
        self.emit('error', title, text)

    def _update_filename(self):
        filename = self.ctrl.filename() or None
        if filename:
            name = os.path.basename(filename)
        else:
            name = "Unsaved"
        self.title.set_text(name)
        self.menu_title.set_text(name)
        self.emit('filename-changed', filename)

    def __getattr__(self, name):
        if name in ["new", "save", "play", "toggle_play", "stop",
                    "goto_start", "goto_end", "select_all",
                    "cut", "copy", "paste", "mix", "undo", "redo",
                    "zoom_in", "zoom_out", "zoom_fit",
                    "select_till_start", "select_till_end",
                    "effect", "open", "save_as", "save_selection_as",
                    "filename", "on_selection_changed"]:
            method = getattr(self.ctrl, name)
            def forward(*args):
                return method(*args)
            return forward
        else:
            raise AttributeError(name)



# -- Tests
           
def test():
    from gum.lib.mock import Fake, Mock
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
    class FakeEditor(Fake):
        def __init__(self):
            self.filename_changed = Fake()
            self.error = Fake()

    notebook = EditorNotebook()
    win = EditorWindow(notebook)
    page = EditorPage(FakeEditor(), graph, selection, cursor)
    notebook.add_page(page)
    win.resize(700, 500)
    win.show_all()
    gtk.main()

    display_error("Title", "Text")

if __name__ == '__main__':
    test()
else:
    # Module is being imported.
    init()
