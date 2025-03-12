from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import Gio
from NLP_Utils import getFileFromPath, OpenPathInFileExplorer
from typing import List
from Entities.NLP_EntityBase import EBase
from Entities.NLP_EntityNote import ENote

class ELibrary(EBase):

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
		super().__init__(file=library, icon='folder')
		self.notes:List[ENote] = []
		self._get_notes(library)

	def open_in_explorer(self):
		OpenPathInFileExplorer(self.get_path())

	def GetNotes(self):
		# TODO accept a function that accepts a JD_EntNode and returns bool. Returns a list of notes compared by that function
		return self.notes;

	# adds a note to the main list and emits signal
	def __add_note(self,note:ENote):
		self.notes.append(note)
		self.signal_note_added.emit(note)
		self.note_deleted_handlers[note] = note.connect('file-deleted', self.__remove_note)

	def __remove_note(self,note:ENote):
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
				self.__add_note(ENote(notes.get_child(note)))
	
	def GetCreateNote(self, filename:str) -> ENote:
		print(f'{DEBUG_PREFIX} Library.GetCreateNote({filename})')
		for note in self.notes:
			if note.get_filename() == filename:
				print(f'{DEBUG_PREFIX} note already exists, returning {note}')
				return note
		# -- create note
		# check if note with this path already exists, and get a ref..
		# If a note with the path already exists, why would 
		note = ENote(getFileFromPath(f'{self.path}/{filename}'))
		if (note.exists() == False):
			template_data = b'this is a test template!'
			note.create(template_data)
		self.__add_note(note)
		return note;