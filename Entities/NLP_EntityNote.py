from NoteLibraryPlugin import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Xed
from gi.repository import Gtk
from gi.repository import Gio
from NLP_Utils import getFileFromPath, readYAML, OpenPathInFileExplorer
import yaml
from Entities.NLP_EntityBase import EBase
from weakref import ref
from typing import Dict,List,Tuple
# BUG ---------------------------
# open a note in a new tab
# move the note to a new window
# open the same note in a new tab (in the new window)
# It will open a duplicate tab instead of referencing the current one
# -------------------------------

class ENote(EBase):
	def __init__(self, file:Gio.File):
		super().__init__(file=file)
		self.file_read:bool = False # True ONLY if readYAML has been called already.
		self.__yaml = None

	@classmethod
	def from_GFileInfo(cls, parent_dir:str, fileInfo:Gio.FileInfo):
		path = f'{parent_dir}/{fileInfo.get_name()}'
		return cls(getFileFromPath(path))

	def open_in_new_tab(self, window:Xed.Window):
		tab:Xed.Tab = window.get_tab_from_location(self.file)
		if tab is None:
			tab = window.create_tab_from_location(self.file,None,0,0,True)
		window.set_active_tab(tab)
		return tab
	
	def open_in_explorer(self):
		OpenPathInFileExplorer(self.get_path().replace(self.get_filename(),''))

	def create(self, template_data):
		outputStream:Gio.FileOutputStream = self.file.create(Gio.FileCreateFlags.NONE)
		outputStream.write_all(template_data)
		outputStream.close()