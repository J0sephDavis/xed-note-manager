from NLP_Utils import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import Gdk
from NLP_Entities import ELibrary, ENote, EBase
from NLP_EntityManager import EntityManager
from NLP_PrivateData import PrivateData
from Panels.NLP_TreeViewUtils import get_entites_from_model, ModelTraverseFlags
from typing import List,Tuple,Dict
from weakref import ref
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

class PanelTab(Gtk.Box):
	def do_deactivate(self):
		print(self.handles)
		for obj in self.handles:
			ent = obj()
			# assumed to be our most common case
			if (type(ent) is ELibrary): self.OnLibraryRemoved(self,ent)
			# uncommon case
			elif type(ent) is None: continue
			else: # default case
				for handle in self.handles[obj]:
					ent.disconnect(handle)
		self.handles.clear()
		self.treeView.get_model().clear()
		self.menu.foreach(lambda widget: widget.destroy())

		self.widget_container = None # TODO move this code into panel.deactivate() method
		self.plugin_private_data = None
		
	def __init__(self, internal_name:str, display_name:str, icon_name:str,
			  window:Xed.Window,ent_tracker:EntityManager, delegate_DailyNoteRoutine):
		self.plugin_private_data = PrivateData()
		self.handles:Dict[ref[GObject.Object],List[int]] = {}
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
		model = self.treeView.get_model()
		model.set_sort_column_id(0, Gtk.SortType.DESCENDING)
		self.treeView.connect("row-activated", self.handler_row_activated, window)
		self.treeView.connect('button-release-event', self.handler_button_release)
		self.pack_start(self.treeView,True,True,0)
		self.show_all()
		# ------------------------ entity tracker handles ------------------------
		tracker_handles = self.handles[ref(ent_tracker)] = []
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
		menu_CreateDailyNote.connect('activate', delegate_DailyNoteRoutine)

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
			if issubclass(type(entry), EBase):
				return model.iter_parent(iter), entry # parent, selected
		return None, None
	
	# Expands the library. Scrolls to the note. Selects the note
	def FocusNote(self, note_path:Gtk.TreePath) -> None:
		library_path:Gtk.TreePath = note_path.copy()
		if (library_path.up() == False):
			print(f'{DEBUG_PREFIX} FocusNote, could not get library_path. note_path:{note_path}')
			return
		self.treeView.expand_row(path=library_path,open_all=False)
		self.treeView.scroll_to_cell(note_path,None,False)
		self.treeView.get_selection().select_path(note_path)

	def GetNote(self, note:ENote) -> Gtk.TreePath|None:
		found =  self.get_entities(note=note,flags=ModelTraverseFlags.EARLY_RETURN | ModelTraverseFlags.RET_PATH)
		if len(found) < 1:
			return None
		return found[0]

	def get_entities(self, note:ENote, flags:ModelTraverseFlags = ModelTraverseFlags.RET_ITER):
		return get_entites_from_model(self.treeView.get_model(), note, flags)

	def handler_CopyFrontmatter(self,widget):
		parent_iter,ent = self.GetCurrentlySelected()
		if (type(ent) != ENote): return
		frontmatter:str = ent.get_yaml_as_str()
		clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		clipboard.set_text(frontmatter, -1)

	def handler_DeleteSelectedFile(self,widget):
		parent_iter,ent = self.GetCurrentlySelected()
		if issubclass(type(ent),EBase) == False: return # override the menu maker / somehow set a sensitivity for what will be shown and not shown (given the current selection)
		ent.delete()

	def handler_OpenNoteInFileExplorer(self, widget):
		parent_iter,ent = self.GetCurrentlySelected()
		if (issubclass(type(ent),EBase)):
			ent.open_in_explorer()

	def handler_CreateDailyNote(self, widget):
		print(f'{DEBUG_PREFIX} handler_CreateDailyNote')
		note = self.plugin_private_data.CreateDailyNote()


	def handler_unimplemented(self, arg):
		print(f'{DEBUG_PREFIX} unimplemented menu item {arg}')

	def handler_button_release(self, view, event):
		if (event.button != 3): return False # Propagate signal
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
		if (type(base) is ENote):
			base.open_in_new_tab(window)
		elif (type(base) is ELibrary):
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

		if (type(entry_ent) is ELibrary):
			self.OnLibraryRemoved(self.handler_remove_selected, entry_ent)
		elif (type(entry_ent) is ENote):
			self.OnNoteRemoved(self.handler_remove_selected, entry_ent)
		else:
			print(f'{DEBUG_PREFIX} ERR remove_selected unhandled entity, {type(entry)} SELECTED[0] {entry[0]} [1]: {entry_ent}')
			# model.remove(selected_iter) # only remove the SELECTED iter
			return

	def OnLibraryAdded(self,caller,library:ELibrary): # called by entity tracker
		print(f'{DEBUG_PREFIX} PanelTab OnLibraryAdded path:{library.path}')
		self.__add_library_signals(ref(library))
		node:Gtk.TreeIter = self.treeView.get_model().append(None, [library.get_filename(), library]) # TODO use a weakref to library in model
		for note in library.notes:
			self.treeView.get_model().append(node, [note.get_filename(), note]) # TODO use a weakref to note in model

	def OnLibraryRemoved(self,caller, library:ELibrary):
		print(f'{DEBUG_PREFIX} PanelTab OnLibraryRemoved {library}')
		self.__remove_library_signals(ref(library))
		
		model:Gtk.TreeStore = self.treeView.get_model()
		removal:List[Gtk.TreeIter] = get_entites_from_model(model,library,ModelTraverseFlags.RET_ITER)
		for iter in removal:
			model.remove(iter)

	def __add_library_signals(self,library_ref:ref[ELibrary]):
		if library_ref in self.handles:
			print(f'{DEBUG_PREFIX} INVALID STATE. library already in handles...')
			self.__remove_library_signals(library_ref)
		else:
			self.handles[library_ref] = []
		handles = self.handles[library_ref]
		handles.append(library_ref().connect('note-added', self.OnNoteAdded))
		handles.append(library_ref().connect('note-removed', self.OnNoteRemoved))

	def __remove_library_signals(self,library_ref:ref[ELibrary]):
		library = library_ref()
		if library is None: return # If called from OnLibraryRemoved, this  should not happen. If called from deactivate(), it might happen.
		for handler in self.handles[library_ref]:
			library.disconnect(handler)

	def OnNoteAdded(self,library:ELibrary, note:ENote):
		print(f'{DEBUG_PREFIX} PanelTab OnNoteAdded {library.path} {note.get_filename()}')
		model = self.treeView.get_model()
		libraries:List[Gtk.TreeIter] = get_entites_from_model(model,library,ModelTraverseFlags.RET_ITER)
		for lib in libraries:
			model.append(lib, [note.get_filename(), note])

	def OnNoteRemoved(self, calling_library:ELibrary|None, note:ENote):
		print(f'{DEBUG_PREFIX} PanelTab OnNoteRemoved {note.get_filename()}')
		model = self.treeView.get_model()
		removal:List[Gtk.TreeIter] = get_entites_from_model(model, note, ModelTraverseFlags.RET_ITER)
		for iter in removal:
			model.remove(iter)