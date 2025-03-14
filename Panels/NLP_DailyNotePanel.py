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
from Entities.NLP_EntityBase import EBase, model_columns
from Entities.NLP_EntityManager import EntityManager
from NLP_PrivateData import PrivateData
from Panels.NLP_TreeViewUtils import get_entites_from_model, ModelTraverseFlags, del_entries_from_model
from Panels.NLP_PanelTabBase import PanelTabBase
from typing import List,Tuple
from weakref import ref

class DailyNotePanel(PanelTabBase):
	name:str = 'daily-note-panel'
	icon_column_index:int = 0
	name_column_index:int = 1
	def __init__(self, window:Xed.Window,
			display_name:str, icon_name:str, library:ELibrary,
			app_level_menu_items:List[Gtk.MenuItem]=[]):
		# ---- list store of treeview
		model:Gtk.ListStore = Gtk.ListStore(str, GObject.TYPE_PYOBJECT, str)
		# ---- init (MUST COME AFTER MODEL) 
		super().__init__(
			window=window,
			treeModel=model,
			internal_name=DailyNotePanel.name,
			display_name=display_name,
			icon_name=icon_name,
			app_level_menu_items=app_level_menu_items,
			panel_level_menu_items=[]
		)
		# ---- treeView (MUST COME AFTER super().__init__())
		self.treeView.insert_column(
			column=Gtk.TreeViewColumn(cell_renderer=Gtk.CellRendererPixbuf(),icon_name=model_columns.ICON),
			position=self.icon_column_index
		)
		name_column = Gtk.TreeViewColumn(title='File Name', cell_renderer=Gtk.CellRendererText(),text=model_columns.NAME)
		self.treeView.insert_column(
			column=name_column,
			position=self.name_column_index
		)
		name_column.set_sort_column_id(model_columns.NAME)
		name_column.set_sort_order(Gtk.SortType.DESCENDING)
		name_column.set_sort_indicator(True)
		# --- library signals
		self.library:ELibrary = library
		lib_handles =  self.handles[ref(self.library)] = []
		lib_handles.append(self.library.connect('note-added', self.OnNoteAdded))
		lib_handles.append(self.library.connect('note-removed', self.OnNoteRemoved))
		for note in library.GetNotes():
			self.treeView.get_model().append(note.create_model_entry())
	# <<< Methods >>>
	def TryFocusNote(self, note:ENote) -> bool:
		# return true on success (note exists in this panel)
		note_path:Gtk.TreePath =  self._get_note(note)
		if (note_path is None):
			return False
		self.treeView.scroll_to_cell(note_path,None,False)
		self.treeView.get_selection().select_path(note_path)
		return True

	# override of base
	def GetCurrentlySelectedLibrary(self)->ref[ELibrary]:
		return ref(self.library)

	# <<< SIGNAL CALLBACKS >>>
	def OnNoteAdded(self,library:ELibrary, note:ENote):
		print(f'{DEBUG_PREFIX} DailyNoteTab OnNoteAdded {library}\t{note}')
		model = self.treeView.get_model()
		model.append(note.create_model_entry())
	
	def OnNoteRemoved(self,library:ELibrary, note:ENote):
		print(f'{DEBUG_PREFIX} DailyNoteTab OnNoteRemoved library:{library}\tnote:{note}')
		model = self.treeView.get_model()
		del_entries_from_model(model,ref(note))