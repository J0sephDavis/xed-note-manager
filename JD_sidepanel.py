from JD__utils import DEBUG_PREFIX, OpenPathInFileExplorer
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from JD__entities import JD_EntLibrary, JD_EntNote, JD_EntBase
from JD_EntManager import EntityManager
from JD_PluginPrivateData import JDPluginPrivate
from typing import List,Tuple
# (later)
# - right click menu to choose whether a file shoudl be opened in a new tab, deleted, moved, &c
# - select multiple notes and open/delete/perform some other action on them
# Aesthetic TODO
# - folder and file icons like the filebrowser sidepanel
# common interfaces for side panel tabs
# - getName()
# - getIcon()
# - getWidget()
# - getStore()

def treeStorePrintRow(store,tPath,tIter):
	print('\t' * (tPath.get_depth()-1), store[tIter][:], sep="")

# used with TreeModel.foreach()
def find_matching_entity(model, path, iter, entity, out_list:List):
		if model[iter][1] == entity: out_list.append(iter)

def GetCurrentlySelected(treeView)->Tuple[Gtk.TreeIter,Gtk.TreeIter]:
	selection = treeView.get_selection()
	if (selection.get_mode() == Gtk.SelectionMode.MULTIPLE):
		print(f'{DEBUG_PREFIX} multiple selection TODO..')
		return None
	(model,iter)=selection.get_selected()
	if (iter is not None):
		entry =  model[iter][1]
		if issubclass(type(entry), JD_EntBase):
			return model.iter_parent(iter), entry # parent, selected
	return None, None

class JDPanelTab(Gtk.Box):
	def __init__(self, internal_name:str, display_name:str, icon_name:str, window:Xed.Window):
		print(f'{DEBUG_PREFIX} PanelTab __init__')
		self.plugin_private_data = JDPluginPrivate()
		super().__init__(spacing=6, orientation=Gtk.Orientation.VERTICAL)

		self.internal_name = internal_name
		self.display_name = display_name
		self.icon_name = icon_name
		
		treeStore:Gtk.TreeStore = Gtk.TreeStore(str, GObject.TYPE_PYOBJECT)
		self.treeView:Gtk.TreeView = Gtk.TreeView(model=treeStore)
		self.treeView.insert_column(
			Gtk.TreeViewColumn(title='name', cell_renderer=Gtk.CellRendererText(),text=0),
			position=-1
		)

		self.libraries_handlers = {}
		
		self.treeView.connect("row-activated", self.handler_row_activated, window)
		self.treeView.connect('button-release-event', self.handler_button_release)
		self.pack_start(self.treeView,True,True,0)
		self.show_all()
		# ------------------------ popup menu ------------------------
		# TODO store handler IDs and remove on __del__
		self.menu_is_open:bool = False
		menu_RemoveSelected = Gtk.MenuItem.new_with_label("Remove selected Entry")
		menu_RemoveSelected.connect('activate', self.handler_remove_selected)

		menu_DeleteSelected = Gtk.MenuItem.new_with_label("Delete Selected Entry")
		menu_DeleteSelected.connect('activate', self.handler_DeleteSelectedFile)
		menu_OpenExplorer = Gtk.MenuItem.new_with_label("Open in File Explorer")
		menu_OpenExplorer.connect('activate', self.handler_OpenNoteInFileExplorer)

		menu_CopyYAML = Gtk.MenuItem.new_with_label("Copy YAML to clipboard") # only show if the selected entity hasattr(yaml)
		menu_CopyYAML.connect('activate', self.handler_unimplemented)

		menu_CreateFromTemplate = Gtk.MenuItem.new_with_label("Create from Template") # include a submenu popout
		menu_CreateFromTemplate.connect('activate', self.handler_unimplemented)

		menu_CreateDailyNote = Gtk.MenuItem.new_with_label("Create Daily Note") # include a submenu popout
		menu_CreateDailyNote.connect('activate', self.handler_CreateDailyNote, window)

		self.menu = Gtk.Menu()
		# --- deal with the currently selected entry ---
		self.menu.append(menu_RemoveSelected)
		self.menu.append(menu_DeleteSelected)
		self.menu.append(menu_OpenExplorer)
		self.menu.append(menu_CopyYAML)
		# --- deals with whichever library the selection is currently within ----
		self.menu.append(Gtk.SeparatorMenuItem())
		self.menu.append(menu_CreateFromTemplate)
		# --- plugin based, no selection needed ---
		self.menu.append(Gtk.SeparatorMenuItem())
		self.menu.append(menu_CreateDailyNote)
		self.menu.show_all()
	
	def handler_DeleteSelectedFile(self,widget):
		parent_iter,ent = GetCurrentlySelected(self.treeView)
		if issubclass(type(ent),JD_EntBase) == False: return # override the menu maker / somehow set a sensitivity for what will be shown and not shown (given the current selection)
		ent.delete()

	def handler_OpenNoteInFileExplorer(self, widget):
		parent_iter,ent = GetCurrentlySelected(self.treeView)
		if (issubclass(type(ent),JD_EntBase)):
			ent.open_in_explorer()

	def handler_CreateDailyNote(self, widget, window):
		print(f'{DEBUG_PREFIX} handler_CreateDailyNote')
		assert window is not None, "window cannot be None"
		note = self.plugin_private_data.CreateDailyNote()
		if note is None: return
		note.open_in_new_tab(window) # TODO, unfold libraries and move the cursor to the note.
		
	def handler_unimplemented(self, arg):
		print(f'{DEBUG_PREFIX} unimplemented menu item {arg}')

	def handler_button_release(self, view, event):
		if (event.button != 3): return False # Propagate signal
		print(f'{DEBUG_PREFIX} handler_button_release {view} {event} x:{event.x} y:{event.y}')

		# If a right click is received, while the menu is closed,
		# the element below the cursor will be selected (GOOD)
		# If a right click is received, while the menu is open,
		# the selection will not be changed (BAD)
		
		# because MenuShell('deactivate') is called when you right click, you can't readily know if the popup WAS open when the user right clicked.
		# there is definitely a way, I just do not know it atm.
		path_tuple = self.treeView.get_path_at_pos(event.x,event.y)
		if (path_tuple is not None and path_tuple[0] is not None):
			self.treeView.set_cursor(path_tuple[0],None,None)
		
		self.menu.popup_at_pointer(event)
		self.menu_is_open = True
		return True # Do not propagate signal

	def GetWidget(self): return self;

	def handler_row_activated(self, treeview, path, col, window):
		count_selection = treeview.get_selection().count_selected_rows()
		print(f'{DEBUG_PREFIX} !!!row-ativated:\n\tpath{path}\n\tselection-size:{count_selection}')
		if count_selection > 1: return
		model = treeview.get_model()
		iter:Gtk.TreeIter = model.get_iter(path)
		base = model[iter][1]
		if (type(base) is JD_EntNote):
			base.open_in_new_tab(window)
		elif (type(base) is JD_EntLibrary):
			base.open_in_explorer()
	
	def handler_remove_selected(self, widget): # maybe rename to handler_close_library
		selection:Gtk.TreeSelection = self.treeView.get_selection()
		selection_mode = selection.get_mode()

		if (selection_mode != Gtk.SelectionMode.SINGLE and selection_mode != Gtk.SelectionMode.BROWSE):
			print(f'{DEBUG_PREFIX} handler_remove_selected get_selected() only supports single selection or browse selection. Use get_selected_rows()\n{selection_mode}')
			return
		
		model,selected_iter = selection.get_selected()
		entry = model[selected_iter]
		if (selected_iter is None):
			print(f'{DEBUG_PREFIX} handler_remove_selected, no entries selected.')
			return
		print(f'{DEBUG_PREFIX} {type(entry)} SELECTED[0] {entry[0]} [1]: {entry[1]}')
		if (type(entry[1]) is JD_EntLibrary):
			print(f'{DEBUG_PREFIX} removing library {entry[0]}')
			self.treeView.get_model().remove(selected_iter)
		else:
			print(f'{DEBUG_PREFIX} selected entry is not a library {entry[0]}, {type(entry[1])}')
			return

	def OnLibraryAdded(self,caller,library:JD_EntLibrary): # called by entity tracker
		print(f'{DEBUG_PREFIX} PanelTab OnLibraryAdded path:{library.path}')
		handlers = self.libraries_handlers[library] = []
		handlers.append(library.connect('note-added', self.OnNoteAdded))
		handlers.append(library.connect('note-removed', self.OnNoteRemoved))

		node:Gtk.TreeIter = self.treeView.get_model().append(None, [library.get_filename(), library])
		for note in library.notes:
			self.treeView.get_model().append(node, [note.get_filename(), note])
	
	def OnLibraryRemoved(self,caller, library:JD_EntLibrary):
		print(f'{DEBUG_PREFIX} PanelTab OnLibraryRemoved path:{library.path}')
		for handler in self.libraries_handlers[library]:
			library.disconnect(handler)
		del self.libraries_handlers[library]
		removal:List[Gtk.TreeIter] = []
		model:Gtk.TreeStore = self.treeView.get_model()
		for node in model:
			if node[1] == library:
				removal.append(node.iter)
		for node in removal:
			model.remove(node)

	def OnNoteAdded(self,library:JD_EntLibrary, note:JD_EntNote):
		print(f'{DEBUG_PREFIX} PanelTab OnNoteAdded {library.path} {note.get_filename()}')
		model = self.treeView.get_model()
		libIter = None
		libraries:List[Gtk.TreeIter] = []
		model.foreach(find_matching_entity, library, libraries)
		for lib in libraries: model.append(lib, [note.get_filename(), note])

	def OnNoteRemoved(self, calling_library:JD_EntLibrary, note:JD_EntNote):
		print(f'{DEBUG_PREFIX} PanelTab OnNoteRemoved {calling_library.path} {note.get_filename()}')
		model = self.treeView.get_model()
		removal:List[Gtk.TreeIter] = []
		model.foreach(find_matching_entity, note,removal)
		for iter in removal:
			model.remove(iter)


class JDSidePanelManager():
	def __init__(self, window:Xed.Window):
		self.PluginPrivateData = JDPluginPrivate()
		self.side_panel = window.get_side_panel()
		self.window = window
		self.entityTracker:EntityManager = self.PluginPrivateData.entTracker
		self.panels:List[JDPanelTab] = []
		print(f'{DEBUG_PREFIX} SidePanelManager __init__')

	def addTab(self, internal_name:str, display_name:str, icon_name:str):
		print(f'{DEBUG_PREFIX} SidePanelManager addTab')
		panel_tab = JDPanelTab(internal_name=internal_name, display_name=display_name, icon_name=icon_name,window=self.window)
		self.side_panel.add_item(panel_tab.GetWidget(),panel_tab.display_name,panel_tab.icon_name)
		self.entityTracker.connect('library-added', panel_tab.OnLibraryAdded)
		self.entityTracker.connect('library-removed', panel_tab.OnLibraryRemoved)
		for library in self.entityTracker.GetLibraries():
			panel_tab.OnLibraryAdded(None, library)
		self.panels.append(panel_tab)

	def getTab(self, tab_internal_name:str) -> JDPanelTab|None:
		for panel in self.panels:
			if panel.internal_name == tab_internal_name:
				return panel
		return None

	def deactivate(self):
		print(f'{DEBUG_PREFIX} JDSidePanelManager.deactivate()')
		for panel in self.panels:
			print(f'{DEBUG_PREFIX} removing panel {panel.internal_name}')
			self.side_panel.remove_item(panel.GetWidget())
			panel.treeView.get_model().clear() # Is this necessary? Or will it be destroyed when we clear the widget.
			panel.widget_container = None # TODO move this code into panel.deactivate() method
		self.panels.clear()
		self.side_panel = None