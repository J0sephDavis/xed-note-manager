from JD__utils import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import Gdk
from JD__entities import JD_EntLibrary, JD_EntNote, JD_EntBase
from JD_PluginPrivateData import JDPluginPrivate
from Panels.TreeViewUtils import get_entites_from_model, ModelTraverseFlags
from typing import List,Tuple,Dict
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

class JDPanelTab(Gtk.Box):
	def __del__(self):
		for obj in self.handles:
			if (type(obj) is JD_EntLibrary):
				self.OnLibraryRemoved(self,obj)
				continue
			for handle in self.handles[obj]:
				obj.disconnect(handle)
		
	def __init__(self, internal_name:str, display_name:str, icon_name:str, window:Xed.Window,ent_tracker:EntityManager):
		print(f'{DEBUG_PREFIX} PanelTab __init__')
		self.plugin_private_data = JDPluginPrivate()
		self.handles:Dict[GObject.Object,List[int]] = {} # Should probably use weakrefs to objects..
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
		self.treeView.connect("row-activated", self.handler_row_activated, window)
		self.treeView.connect('button-release-event', self.handler_button_release)
		self.pack_start(self.treeView,True,True,0)
		self.show_all()
		# ------------------------ entity tracker handles ------------------------
		tracker_handles = self.handles[ent_tracker] = []
		tracker_handles.append(ent_tracker.connect('library-added',self.OnLibraryAdded))
		tracker_handles.append(ent_tracker.connect('library-removed', self.OnLibraryRemoved))
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
		menu_CopyYAML.connect('activate', self.handler_CopyFrontmatter)

		menu_CreateFromTemplate = Gtk.MenuItem.new_with_label("Create from Template") # include a submenu popout
		menu_CreateFromTemplate.connect('activate', self.handler_unimplemented)

		menu_CreateDailyNote = Gtk.MenuItem.new_with_label("Create Daily Note") # include a submenu popout
		menu_CreateDailyNote.connect('activate', self.handler_CreateDailyNote)

		self.menu = Gtk.Menu()
		# TODO, can we use action groups here? Then we can set sensitivity on some groups so they may not appear
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
	
	def GetCurrentlySelected(self)->Tuple[Gtk.TreeIter,Gtk.TreeIter]:
		selection = self.treeView.get_selection()
		if (selection.get_mode() == Gtk.SelectionMode.MULTIPLE):
			print(f'{DEBUG_PREFIX} multiple selection TODO..')
			return None
		(model,iter)=selection.get_selected()
		if (iter is not None):
			entry =  model[iter][1]
			if issubclass(type(entry), JD_EntBase):
				return model.iter_parent(iter), entry # parent, selected
		return None, None
	
	def handler_CopyFrontmatter(self,widget):
		parent_iter,ent = self.GetCurrentlySelected()
		if (type(ent) != JD_EntNote): return
		frontmatter:str = ent.get_yaml_as_str()
		clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		clipboard.set_text(frontmatter, -1)

	def handler_DeleteSelectedFile(self,widget):
		parent_iter,ent = self.GetCurrentlySelected()
		if issubclass(type(ent),JD_EntBase) == False: return # override the menu maker / somehow set a sensitivity for what will be shown and not shown (given the current selection)
		ent.delete()

	def handler_OpenNoteInFileExplorer(self, widget):
		parent_iter,ent = self.GetCurrentlySelected()
		if (issubclass(type(ent),JD_EntBase)):
			ent.open_in_explorer()

	def handler_CreateDailyNote(self, widget, window):
		print(f'{DEBUG_PREFIX} handler_CreateDailyNote')
		assert window is not None, "window cannot be None"
		note = self.plugin_private_data.CreateDailyNote()
		if note is None: return
		note.open_in_new_tab(window)
		self.ScrollToNote(note)
	
	def handler_NoteFocus(self, caller, note:JD_EntNote):
		self.ScrollToNote(note)

	def ScrollToNote(self,note:JD_EntNote): # maybe this should become the result of a signal being received? note-request-focus(note)
		model = self.treeView.get_model()
		flags:ModelTraverseFlags = ModelTraverseFlags.EARLY_RETURN | ModelTraverseFlags.RET_PATH
		found:List[Gtk.TreePath] = get_entites_from_model(model,note,flags)
		if (len(found) < 1): return
		path:Gtk.TreePath = found[0]
		libpath:Gtk.TreePath = path.copy()
		if (libpath.up() == False): raise Exception('state error. cannot get library from note\'s path')
		self.treeView.expand_row(path=libpath, open_all=False)
		self.treeView.get_selection().select_path(path)
		self.treeView.scroll_to_cell(found[0],None,False)

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
		if count_selection > 1: return
		model = treeview.get_model()
		iter:Gtk.TreeIter = model.get_iter(path)
		base = model[iter][1]
		if (type(base) is JD_EntNote):
			base.open_in_new_tab(window)
		elif (type(base) is JD_EntLibrary):
			base.open_in_explorer()
	
	# DEBUG only. Remove in PROD
	# removes the selected entity from the model (removes ALL of them)
	def handler_remove_selected(self, widget):
		selection:Gtk.TreeSelection = self.treeView.get_selection()
		selection_mode = selection.get_mode()

		if (selection_mode != Gtk.SelectionMode.SINGLE and selection_mode != Gtk.SelectionMode.BROWSE):
			print(f'{DEBUG_PREFIX} handler_remove_selected get_selected() only supports single selection or browse selection. Use get_selected_rows()\n{selection_mode}')
			return
		
		model,selected_iter = selection.get_selected()
		entry = model[selected_iter]
		entry_ent = entry[1]
		if (selected_iter is None): return

		print(f'{DEBUG_PREFIX} {type(entry)} SELECTED[0] {entry[0]} [1]: {entry_ent}')
		if (type(entry_ent) is JD_EntLibrary):
			self.OnLibraryRemoved(self.handler_remove_selected, entry_ent)
		elif (type(entry_ent) is JD_EntNote):
			self.OnNoteRemoved(self.handler_remove_selected, entry_ent)
		else:
			print(f'{DEBUG_PREFIX} remove_selected unhandled entity')
			# model.remove(selected_iter) # only remove the SELECTED iter
			return

	def OnLibraryAdded(self,caller,library:JD_EntLibrary): # called by entity tracker
		print(f'{DEBUG_PREFIX} PanelTab OnLibraryAdded path:{library.path}')
		handlers = self.handles[library] = []
		handlers.append(library.connect('note-added', self.OnNoteAdded))
		handlers.append(library.connect('note-removed', self.OnNoteRemoved))

		node:Gtk.TreeIter = self.treeView.get_model().append(None, [library.get_filename(), library])
		for note in library.notes:
			self.treeView.get_model().append(node, [note.get_filename(), note])
	
	def OnLibraryRemoved(self,caller, library:JD_EntLibrary):
		print(f'{DEBUG_PREFIX} PanelTab OnLibraryRemoved {library}')
		for handler in self.handles[library]:
			library.disconnect(handler)
		del self.handles[library]
		model:Gtk.TreeStore = self.treeView.get_model()
		removal:List[Gtk.TreeIter] = get_entites_from_model(model,library,ModelTraverseFlags.RET_ITER)
		for iter in removal:
			model.remove(iter)

	def OnNoteAdded(self,library:JD_EntLibrary, note:JD_EntNote):
		print(f'{DEBUG_PREFIX} PanelTab OnNoteAdded {library.path} {note.get_filename()}')
		model = self.treeView.get_model()
		libraries:List[Gtk.TreeIter] = get_entites_from_model(model,library,ModelTraverseFlags.RET_ITER)
		for lib in libraries:
			model.append(lib, [note.get_filename(), note])

	def OnNoteRemoved(self, calling_library:JD_EntLibrary|None, note:JD_EntNote):
		print(f'{DEBUG_PREFIX} PanelTab OnNoteRemoved {note.get_filename()}')
		model = self.treeView.get_model()
		removal:List[Gtk.TreeIter] = get_entites_from_model(model, note, ModelTraverseFlags.RET_ITER)
		for iter in removal:
			model.remove(iter)