from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
from weakref import ref
class EBase(GObject.Object):
	# ------------------------------ signals -------------------------------------
	@GObject.Signal(name='file-deleted', flags=GObject.SignalFlags.RUN_LAST)
	def signal_file_deleted(self_note):
		print(f'{DEBUG_PREFIX} Entity SIGNAL deleted')
	# ------------------------------ class -------------------------------------
	def open_in_explorer(self): pass

	def __init__(self, file:Gio.File, icon:str):
		super().__init__()
		self.file = file
		self.icon_str = icon
	
	def get_filename(self): return self.file.get_basename()
	def get_path(self): return self.file.get_path()
	def get_icon(self): return self.icon_str # return the icon which the entity wants to be displayed with
	# used when creating a TreeModel entry
	def create_model_entry(self): return [self.get_filename(), ref(self),self.get_icon()]

	def exists(self):
		return self.file.query_exists()
	
	def delete(self):
		try:
			self.file.delete()
		except GLib.Error as e: # Probably folder not empty.
			print(f'EXCEPTION EBase::delete(self) GLib.Error({e.code}): {e.message}')
		if self.exists() == False:
			self.signal_file_deleted.emit()
