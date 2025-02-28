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
from JD__utils import getFileFromPath, readYAML
from typing import List
import weakref

class JD_EntBase(): # TODO: use as the base  for the TreeModel entries? With a getModel() command?
	# File
	# File Name
	# Display Name
	# Sort Name?

	def __init__(self, file:Gio.File):
		self.file = file;
	
	def getFilename(self): return self.file.get_basename()


class JD_EntNote(JD_EntBase):

	def __init__(self, file:Gio.File):
		super().__init__(file=file)
		
		self.file_read:bool = False # True ONLY if readYAML has been called already.
		self.__yaml = None

	@classmethod
	def from_GFileInfo(cls, parent_dir:str, fileInfo:Gio.FileInfo):
		path = f'{parent_dir}/{fileInfo.get_name()}'
		return cls(getFileFromPath(path))
		pass

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
		self.__yaml = readYAML(self.path)
		return self.__yaml

class JD_EntLibrary(JD_EntBase):
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
		self.path = library_path
		print(f'{DEBUG_PREFIX} library_path: {self.path}')
		library:Gio.File = getFileFromPath(self.path) # TODO try-except to get the dir
		super().__init__(file=library)
		self.notes:List[JD_EntNote] = []
		self._get_notes(library)
		self.note_added_callbacks = []
		self.note_removed_callbacks = []

	def GetNotes(self):
		# TODO accept a function that accepts a JD_EntNode and returns bool. Returns a list of notes compared by that function
		return self.notes;

	def _get_notes(self, library:Gio.File):
		notes = library.enumerate_children(
			self.search_attributes,
			Gio.FileQueryInfoFlags.NONE,
			None
		)
		for note in notes:
			# TODO name filters (self.regex_filter & class.regex_filter)
			if note.get_file_type() == Gio.FileType.REGULAR: # TODO reevaluate filter on FileType
				self.notes.append(JD_EntNote.from_GFileInfo(self.path, note))
	
	def GetCreateNote(self, filename:str) -> JD_EntNote:
		print(f'{DEBUG_PREFIX} Library.GetCreateNote({filename})')
		for note in self.notes:
			if note.getFilename() == filename:
				print(f'{DEBUG_PREFIX} note already exists, returning {note}')
				return note
		# -- create note
		file:Gio.File = getFileFromPath(f'{self.path}/{filename}')
		if (file.query_exists()):
			print(f'{DEBUG_PREFIX} This should not happen. If the file exists, it should have been present in self.notes')
			assert False, "state error"
		outputStream:Gio.FileOutputStream = file.create(Gio.FileCreateFlags.NONE)
		template_data = b'this is a test template!'
		outputStream.write_all(template_data)
		outputStream.close()
		note = JD_EntNote(file=file)
		self.notes.append(note)
		self.AnnounceNoteAdded(note)
		return note;


	def SubscribeNoteAdded(self, callback):
		print(f'{DEBUG_PREFIX} subscribe note added {callback}')
		self.note_added_callbacks.append(weakref.WeakMethod(callback))

	def SubscribeNoteRemoved(self, callback):
		print(f'{DEBUG_PREFIX} subscribe note removed {callback}')
		self.note_removed_callbacks.append(weakref.WeakMethod(callback))

	def UnsubscribeNoteAdded(self,callback):
		print(f'{DEBUG_PREFIX} unsubscribe note added {callback}')
		remove_me = None
		for cb in self.note_added_callbacks:
			if cb() == callback:
				remove_me = cb
				break
		if (remove_me is None):
			print(f'{DEBUG_PREFIX} cannot unsubscribe, no matching callback')
			return
		self.note_added_callbacks.remove(remove_me)
		print(f'{DEBUG_PREFIX} unsubscribed {remove_me}')
		
	def UnsubscribeNoteRemoved(self,callback):
		print(f'{DEBUG_PREFIX} unsubscribe note removed {callback}')
		remove_me = None
		for cb in self.note_added_callbacks:
			if cb() == callback:
				remove_me = cb
				break
		if (remove_me is None):
			print(f'{DEBUG_PREFIX} cannot unsubscribe, no matching callback')
			return
		self.note_added_callbacks.remove(remove_me)
		print(f'{DEBUG_PREFIX} unsubscribed {remove_me}')

	def AnnounceNoteAdded(self, note:JD_EntNote):
		for cb in self.note_added_callbacks:
			cb()(self,note)

	def AnnounceNoteRemoved(self,  note:JD_EntNote):
		for cb in self.note_removed_callbacks:
			cb()(self,note)