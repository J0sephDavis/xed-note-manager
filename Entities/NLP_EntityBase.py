from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
from weakref import ref
from typing import List,Dict
from enum import Enum

class model_columns(Enum): # see EBase:create_model_entry(...)
	FILENAME 	= 0
	REF			= 1
	ICON		= 2

# IS-A file. What would be the detriment to making EBase inherit from Gio.File? Do we still have access to making signals?
class EBase(GObject.Object):
	# ------------------------------ signals -------------------------------------
	@GObject.Signal(name='file-deleted', flags=GObject.SignalFlags.RUN_LAST)
	def signal_file_deleted(self_note): print(f'{DEBUG_PREFIX} Entity SIGNAL deleted')
	# ------------------------------ class -------------------------------------
	def open_in_explorer(self):	raise NotImplementedError("EBase:open_in_explorer not implemented") # must be set in inherited class. (to choose whether you want get_dir or get_path)

	def __init__(self, file:Gio.File, icon:str='face-devilish'):
		GObject.Object.__init__(self)
		self.handlers:Dict[ref[GObject.Object], List[int]] = {}
		self.file = file
		self.icon = icon

	def create_model_entry(self): 	return [self.get_filename(), ref(self),self.get_icon()]
	def get_icon(self)->str: 		return self.icon
	
	def get_filename(self)->str:	return self.file.get_basename()
	def get_path(self)->str: 		return self.file.get_path()
	def get_base_dir(self)->str: 	return self.file.get_path()[:-len(self.get_filename())]
	
	def exists(self)->bool:			return self.file.query_exists()
	
	def delete(self)->None:
		try:
			self.file.delete()
		except GLib.Error as e: # Probably folder not empty.
			print(f'EXCEPTION EBase::delete(self) GLib.Error({e.code}): {e.message}')
		if self.exists() == False:
			self.signal_file_deleted.emit()
