from NLP_Utils import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import Gdk
from Entities.NLP_EntityLibrary import ELibrary
from Entities.NLP_EntityNote import ENote
from Entities.NLP_EntityBase import EBase
from Entities.NLP_EntityManager import EntityManager
from NLP_PrivateData import PrivateData
from Panels.NLP_TreeViewUtils import get_entites_from_model, ModelTraverseFlags, del_entries_from_model
from Panels.NLP_PanelTabBase import PanelTabBase
from typing import List,Tuple
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

class LibraryPanelTab(PanelTabBase):
	def __init__(self, window:Xed.Window, internal_name:str, display_name:str, icon_name:str,
				ent_tracker:EntityManager, delegate_DailyNoteRoutine):
		treeStore:Gtk.TreeStore = Gtk.TreeStore(str, GObject.TYPE_PYOBJECT)
		super().__init__(
			window=window,
			treeModel=treeStore,
			internal_name=internal_name,
			display_name=display_name,
			icon_name=icon_name
		)
		self.treeView.insert_column(
			column=Gtk.TreeViewColumn(title='File Name', cell_renderer=Gtk.CellRendererText(),text=0),
			position=-1
		)
		treeStore.set_sort_column_id(0, Gtk.SortType.DESCENDING)

		# ----- entity tracker handles -----
		tracker_handles = self.handles[ref(ent_tracker)] = []
		tracker_handles.append(ent_tracker.connect('library-added',self.OnLibraryAdded))
		tracker_handles.append(ent_tracker.connect('library-removed', self.OnLibraryRemoved))
		
		# ------------------------ popup menu ------------------------
		# TODO store handler IDs and remove on __del__
		self.menu_is_open:bool = False
		menu_DeleteSelected = Gtk.MenuItem.new_with_label("Delete Selected Entry")
		menu_DeleteSelected.connect('activate', self.handler_DeleteSelectedFile)
		
		menu_OpenExplorer = Gtk.MenuItem.new_with_label("Open in File Explorer")
		menu_OpenExplorer.connect('activate', self.handler_OpenNoteInFileExplorer)

		menu_CreateDailyNote = Gtk.MenuItem.new_with_label("Create Daily Note") # include a submenu popout
		menu_CreateDailyNote.connect('activate', delegate_DailyNoteRoutine)

		# TODO, can we use action groups here? Then we can set sensitivity on some groups so they may not appear
		# --- deal with the currently selected entry ---
		self.menu.append(menu_DeleteSelected)
		self.menu.append(menu_OpenExplorer)
		# --- plugin based, no selection needed ---
		self.menu.append(Gtk.SeparatorMenuItem())
		self.menu.append(menu_CreateDailyNote)
		self.menu.show_all()
	
	def TryFocusNote(self, note:ENote) -> bool:
		note_path:Gtk.TreePath = self._get_note(note)
		if (note_path is None):
			return False
		library_path:Gtk.TreePath = note_path.copy()
		if (library_path.up() == False):
			print(f'{DEBUG_PREFIX} FocusNote, could not get library_path. note_path:{note_path}')
			return False
		self.treeView.expand_row(path=library_path,open_all=False)
		self.treeView.scroll_to_cell(note_path,None,False)
		self.treeView.get_selection().select_path(note_path)
		return True

	def handler_CopyFrontmatter(self,widget):
		ent = self.GetCurrentlySelected()[1]()
		if (type(ent) != ENote): return
		frontmatter:str = ent.get_yaml_as_str()
		clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		clipboard.set_text(frontmatter, -1)

	def handler_DeleteSelectedFile(self,widget):
		ent = self.GetCurrentlySelected()[1]()
		if issubclass(type(ent),EBase) == False: return # override the menu maker / somehow set a sensitivity for what will be shown and not shown (given the current selection)
		ent.delete()

	def handler_OpenNoteInFileExplorer(self, widget):
		ent = self.GetCurrentlySelected()[1]()
		if (issubclass(type(ent),EBase)):
			ent.open_in_explorer()

	def handler_CreateDailyNote(self, widget):
		print(f'{DEBUG_PREFIX} handler_CreateDailyNote')
		note = self.plugin_private_data.CreateDailyNote()

	def handler_unimplemented(self, arg):
		print(f'{DEBUG_PREFIX} unimplemented menu item {arg}')

	# DEBUG only. Remove in PROD
	# removes the selected entity from the model (removes ALL of them)
	def handler_remove_selected(self, widget):
		entry_ent = self.GetCurrentlySelected()[1]()
		if (entry_ent is None): return
		if (type(entry_ent) is ELibrary):
			self.OnLibraryRemoved(self.handler_remove_selected, entry_ent)
		elif (type(entry_ent) is ENote):
			self.OnNoteRemoved(self.handler_remove_selected, entry_ent)
		else:
			print(f'{DEBUG_PREFIX} ERR remove_selected unhandled entity, {type(entry_ent)}')
			return

	def AddLibraries(self, libraries:List[ELibrary]):
		for lib in libraries:
			self.OnLibraryAdded(None,lib)

	def OnLibraryAdded(self,caller,library:ELibrary): # called by entity tracker
		print(f'{DEBUG_PREFIX} PanelTab OnLibraryAdded path:{library.path}')
		self.__add_library_signals(ref(library))
		node:Gtk.TreeIter = self.treeView.get_model().append(None, [library.get_filename(), ref(library)])
		for note in library.notes:
			self.treeView.get_model().append(node, [note.get_filename(), ref(note)])

	def OnLibraryRemoved(self,caller, library:ELibrary):
		print(f'{DEBUG_PREFIX} PanelTab OnLibraryRemoved {library}')
		lib_ref = ref(library)
		self.__remove_library_signals(lib_ref)
		del_entries_from_model(self.treeView.get_model(),lib_ref)

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
		libraries:List[Gtk.TreeIter] = get_entites_from_model(model,ref(library),ModelTraverseFlags.RET_ITER)
		for lib in libraries:
			model.append(lib, [note.get_filename(), ref(note)])

	def OnNoteRemoved(self, calling_library:ELibrary|None, note:ENote):
		print(f'{DEBUG_PREFIX} PanelTab OnNoteRemoved {note.get_filename()}')
		model = self.treeView.get_model()
		del_entries_from_model(model,ref(note))