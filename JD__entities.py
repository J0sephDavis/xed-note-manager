from JD_dailynotes import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import PeasGtk
from gi.repository import GLib
from gi.repository import Gio
from JD__utils import getFileFromPath, readYAML, OpenPathInFileExplorer
from typing import List
import weakref
import yaml

class JD_EntBase(GObject.Object):
	# ------------------------------ signals -------------------------------------
	@GObject.Signal(name='file-deleted', flags=GObject.SignalFlags.RUN_LAST)
	def signal_file_deleted(self_note):
		print(f'{DEBUG_PREFIX} Entity SIGNAL deleted')
	# ------------------------------ class -------------------------------------
	def open_in_explorer(self): pass

	def __init__(self, file:Gio.File):
		super().__init__()
		self.file = file;
	
	def get_filename(self): return self.file.get_basename()
	def get_path(self): return self.file.get_path()
	
	def exists(self):
		return self.file.query_exists()
	
	def delete(self):
		try:
			self.file.delete()
		except GLib.Error as e: # Probably folder not empty.
			print(f'EXCEPTION JD_EntBase::delete(self) GLib.Error({e.code}): {e.message}')
		if self.exists() == False:
			self.signal_file_deleted.emit()

class JD_EntNote(JD_EntBase):
	def __init__(self, file:Gio.File):
		super().__init__(file=file)
		
		self.file_read:bool = False # True ONLY if readYAML has been called already.
		self.__yaml = None

	@classmethod
	def from_GFileInfo(cls, parent_dir:str, fileInfo:Gio.FileInfo):
		path = f'{parent_dir}/{fileInfo.get_name()}'
		return cls(getFileFromPath(path))

	def open_in_new_tab(self, window:Xed.Window): # window is the main Xed window
		# TODO, If window is already open, focus tab instead of opening a new one.
		# Make configurable? Or accelerator defined, like ctrl+activate opens regardless.
		window.create_tab_from_location(
			self.file,
			None,0,0,True
		)
	
	def get_yaml(self) -> object:
		print(f'{DEBUG_PREFIX} get_frontmatter')
		if (self.file_read):
			return self.__yaml;
		self.file_read = True
		self.__yaml = readYAML(self.get_path())
		return self.__yaml
		
	def get_yaml_as_str(self) -> str|None:
		print(f'{DEBUG_PREFIX} get_frontmatter (str)')
		_yaml = self.get_yaml()
		if _yaml is None: return None
		return yaml.dump(_yaml)
	
	def open_in_explorer(self):
		OpenPathInFileExplorer(self.get_path().replace(self.get_filename(),''))

	def create(self, template_data):
		outputStream:Gio.FileOutputStream = self.file.create(Gio.FileCreateFlags.NONE)
		outputStream.write_all(template_data)
		outputStream.close()


class JD_EntLibrary(JD_EntBase):

	@GObject.Signal(name='note-added', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_note_added(self_library, note):
		print(f'{DEBUG_PREFIX} Library SIGNAL - note-added')

	@GObject.Signal(name='note-removed', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_note_removed(self_library, note):
		print(f'{DEBUG_PREFIX} Library SIGNAL - note-removed')
	
	# Overview of attributes https://docs.gtk.org/gio/file-attributes.html
	# All attributes https://stuff.mit.edu/afs/sipb/project/barnowl/share/gtk-doc/html/gio/gio-GFileAttribute.html
	# https://lazka.github.io/pgi-docs/Gio-2.0/flags.html#Gio.FileQueryInfoFlags # TODO configurable
	search_attributes = ",".join([
		r'standard::name',
		r'standard::content-type',
		r'standard::type',
		r'standard::size',
		r'time::modified',
		r'access::can_read',
	]);
	
	def __init__(self, library_path:str):
		self.note_deleted_handlers = {}
		self.path = library_path
		print(f'{DEBUG_PREFIX} library_path: {self.path}')
		library:Gio.File = getFileFromPath(self.path) # TODO try-except to get the dir
		super().__init__(file=library)
		self.notes:List[JD_EntNote] = []
		self._get_notes(library)

	def open_in_explorer(self):
		OpenPathInFileExplorer(self.get_path())

	def GetNotes(self):
		# TODO accept a function that accepts a JD_EntNode and returns bool. Returns a list of notes compared by that function
		return self.notes;

	# adds a note to the main list and emits signal
	def __add_note(self,note:JD_EntNote):
		self.notes.append(note)
		self.signal_note_added.emit(note)
		self.note_deleted_handlers[note] = note.connect('file-deleted', self.__remove_note)

	def __remove_note(self,note:JD_EntNote):
		print(f'{DEBUG_PREFIX} remove note')
		note.disconnect(self.note_deleted_handlers[note])
		self.signal_note_removed.emit(note)
		self.notes.remove(note)

	def _get_notes(self, library:Gio.File):
		notes = library.enumerate_children(
			self.search_attributes,
			Gio.FileQueryInfoFlags.NONE,
			None
		)
		for note in notes:
			# TODO name filters (self.regex_filter & class.regex_filter)
			if note.get_file_type() == Gio.FileType.REGULAR: # TODO reevaluate filter on FileType
				self.__add_note(JD_EntNote.from_GFileInfo(self.path, note))
	
	def GetCreateNote(self, filename:str) -> JD_EntNote:
		print(f'{DEBUG_PREFIX} Library.GetCreateNote({filename})')
		for note in self.notes:
			if note.get_filename() == filename:
				print(f'{DEBUG_PREFIX} note already exists, returning {note}')
				return note
		# -- create note
		# check if note with this path already exists, and get a ref..
		# If a note with the path already exists, why would 
		note = JD_EntNote(getFileFromPath(f'{self.path}/{filename}'))
		if (note.exists() == False):
			template_data = b'this is a test template!'
			note.create(template_data)
		self.__add_note(note)
		return note;