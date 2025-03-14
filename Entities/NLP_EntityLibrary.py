from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import Gio
from NLP_Utils import getFileFromPath, OpenPathInFileExplorer, new_unique_file
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
		self.templates:List[ENote] = []
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
				gfile = notes.get_child(note)
				if note.get_name().startswith('.template'):
					self.templates.append(ENote(gfile))
				else:
					self.__add_note(ENote(gfile))
	
	# initial_content: If we create the file, this will be the content of the file.
	def CreateNote(self, filename:str,initial_content:bytes=None) -> ENote:
		print(f'{DEBUG_PREFIX} Library.CreateNote({filename})')
		for note in self.notes: # Check the KNOWN notes or this file.
			if note.get_filename() == filename:
				return note
		note = ENote(getFileFromPath(f'{self.path}/{filename}')) # NOTE filesystem specific separator...
		if (note.exists() == False):
			note.create(initial_content)
		#---
		self.__add_note(note)
		return note;

	def CreateUniqueNote(self, initial_content:bytes=None)->ENote:
		file = new_unique_file(self.file, 'note')
		if file is None: raise RuntimeError("(DESCRIPTIVE ERROR) oops")
		note = ENote(file)
		if (note.exists()): raise RuntimeError("File should have been unique; however, it already exists.")
		note.create(initial_content)
		self.__add_note(note)
		return note

	def GetTemplates(self) -> List[ENote]: # return as a list of ENotes, or maybe make a new entity to represent a template? or just use the Gio.File
		return self.templates