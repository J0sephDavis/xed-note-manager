from NoteLibraryPlugin import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Xed
from gi.repository import Gtk
from gi.repository import Gio
from NLP_Utils import OpenPathInFileExplorer
from Entities.NLP_EntityBase import EBase
# BUG ---------------------------
# open a note in a new tab
# move the note to a new window
# open the same note in a new tab (in the new window)
# It will open a duplicate tab instead of referencing the current one
# -------------------------------

class ENote(EBase):
	def __init__(self, file:Gio.File):
		super().__init__(file=file,icon='text-x-generic')

	def open_in_explorer(self): OpenPathInFileExplorer(self.get_base_dir())

	def open_in_new_tab(self, window:Xed.Window)->Xed.Tab:
		tab:Xed.Tab = window.get_tab_from_location(self.file)
		if tab is None:
			tab = window.create_tab_from_location(self.file,None,0,0,True)
		window.set_active_tab(tab)
		return tab
	
	# @classmethod
	# def from_template(cls, template:ETemplate, library:ELibrary, make_unique:bool=False):
	# 	t_name = template.ChooseFileName(library)
	# 	t_data = template.GetContents()
	# 	file:Gio.File =  library.file.get_child(t_name)
	# 	if file.exists() == False:
	# 		return ENote(file).save_file(t_data)
	# 	if t_name is None: t_name = 'note'
	# 	new_unique_file(library.file,t_name)