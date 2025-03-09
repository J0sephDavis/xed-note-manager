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

class DailyNotePanel(PanelTabBase):
	def __init__(self, window:Xed.Window,display_name:str, internal_name:str, icon_name:str, library:ELibrary):
		self.library:ELibrary = library
		model:Gtk.ListStore = Gtk.ListStore(str, GObject.TYPE_PYOBJECT)
		super().__init__(
			window=window,
			treeModel=model,
			internal_name=internal_name,
			display_name=display_name,
			icon_name=icon_name
		)
		viewColumn = Gtk.TreeViewColumn(title='File Name', cell_renderer=Gtk.CellRendererText(),text=0)
		self.treeView.insert_column(
			column=viewColumn,
			position=-1
		)
		# TODO why does this not accept the sort type? See PanelTab for how its done. it uses the tree view?
		viewColumn.set_sort_column_id(0) #,Gtk.SortType.DESCENDING
		self.treeView.get_model().set_sort_column_id(0, Gtk.SortType.DESCENDING)
		for note in library.GetNotes():
			self.treeView.get_model().append([note.get_filename(), ref(note)])

		self.menu_is_open:bool = False
		self.menu.show_all()
	# <<< Methods >>>
	def TryFocusNote(self, note:ENote) -> bool:
		# return true on success (note exists in this panel)
		note_path:Gtk.TreePath =  self._get_note(note)
		if (note_path is None):
			return False
		self.treeView.scroll_to_cell(note_path,None,False)
		self.treeView.get_selection().select_path(note_path)
		return True

	# <<< SIGNAL CALLBACKS >>>
	def OnNoteAdded(self,library:ELibrary, note:ENote):
		print(f'{DEBUG_PREFIX} DailyNoteTab OnNoteAdded {library}\t{note}')
		model = self.treeView.get_model()
		model.append([note.get_filename(),ref(note)])
	
	def OnNoteRemoved(self,library:ELibrary, note:ENote):
		print(f'{DEBUG_PREFIX} DailyNoteTab OnNoteRemoved library:{library}\tnote:{note}')
		model = self.treeView.get_model()
		del_entries_from_model(model,ref(note))