from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import Gio
from NLP_Utils import getFileFromPath, OpenPathInFileExplorer, new_unique_file
from typing import List,Callable,Dict
from Entities.NLP_EntityBase import EBase
from Entities.NLP_EntityNote import ENote
from Entities.NLP_EntityTemplate import ETemplate
from weakref import ref
from datetime import datetime

def str_utf8(val)->bytes: return str(val).encode("utf-8")

class ELibrary(EBase):
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
	
	@classmethod
	def from_path(cls,path:str): return cls(getFileFromPath(path))
	# ----- signals -----
	@GObject.Signal(name='note-added', flags=GObject.SignalFlags.RUN_FIRST, arg_types=(GObject.TYPE_PYOBJECT,))
	def _signal_note_added(self,note:ENote): # RUN_FIRST
		self.notes.append(note)
		nref = ref(note)
		if nref not in self.handlers:
			self.handlers[ref(note)] = []
		handles:List[int] = self.handlers[ref(note)]
		handles.append(note.connect('file-deleted', self._signal_note_removed.emit))
	@GObject.Signal(name='note-removed', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def _signal_note_removed(self,note:ENote): # RUN_FIRST
		self.notes.append(note)
		nref = ref(note)
		if nref not in self.handlers:
			return
		handles:List[int] = self.handlers[ref(note)]
		for id in handles:
			note.disconnect(id)
		self.notes.remove(note)
	# ----- virtual base class methods -----
	def open_in_explorer(self): OpenPathInFileExplorer(self.get_path())
	# ----- class-instance -----
	def __init__(self, file:Gio.File): # Libraries are generally created from the config, which has paths
		EBase.__init__(self,file,'folder')
		self.notes:List[ENote] = []
		self.templates:List[ETemplate] = []
		self.__get_notes_from_dir(no_clobber=False, emit_signals=False)

		# TODO check for a .info or .nfo folder that has a yaml dictionary of values and merge it with this.
		# the .info/nfo file should take precedence over the defaults.
		self.metadata:(Dict[bytes,
					  bytes| Callable[[bytes],bytes]| Callable[[bytes,Dict],bytes]]) = {
						  # --- library specific
						  b'folder_name': lambda bstr: str_utf8(self.get_filename()),
						  b'folder_path': lambda bstr: str_utf8(self.get_path()),
						  b'folder_dir': lambda bstr: str_utf8(self.get_base_dir()),
						  # --- TODO factor these out
						  b'time_now': lambda bstr: str_utf8(datetime.now()),
		}
	
	def __get_notes_from_dir(self, no_clobber:bool = True, emit_signals:bool = True):
		add_note:Callable[[ENote],None] = self._signal_note_added.emit if emit_signals else self._signal_note_added
		add_template = self.templates.append
		# ---
		directory_enumerator:Gio.FileEnumerator = self.file.enumerate_children(
			self.search_attributes,
			Gio.FileQueryInfoFlags.NONE,
			None
		)
		# ---
		file_info:Gio.FileInfo = None
		ent:ETemplate|ENote = None
		arr:List[ETemplate]|List[ENote] = None
		for file_info in directory_enumerator:
			if file_info.get_file_type() != Gio.FileType.REGULAR: continue
			file:Gio.File = directory_enumerator.get_child(file_info)
			if file_info.get_name().startswith('.template'):
				ent = ETemplate(file)
				arr = self.templates
				append = add_template
			else:
				ent = ENote(file)
				arr = self.notes
				append = add_note
			if no_clobber and ent in arr: continue
			append(ent)
	# Get Notes
	def GetNotes(self)->List[ENote]: return self.notes
	def GetNoteByName(self,name:str)->ENote|None:
		note:ENote|None = None
		for note in self.notes:
			if note.get_filename() == name: break
		return note
	def GetNoteByFile(self,file:Gio.File)->ENote|None:
		note:ENote|None = None
		for note in self.notes:
			if note.file == file: break
		return note
	# Get Templates
	def GetTemplates(self)->List[ETemplate]: return self.templates
	def GetTemplateByName(self,name:str)->ETemplate:
		template:ETemplate|None = None
		for template in self.templates:
			if template.get_filename() == name: break # TODO implement an EBase.get_name() for a generic name? for notes it would be the file name. libraries dir name, and templates maybe a user-provided name
		return template
	
	## Create files
	# Returns None when a note with the corresponding Gio.File
	# Returns ENote when an Enote did not already exist with this files name
	# TODO should it also return None when an ENote did note exist, but file.exists() returns True? I think this is the callers problem tbh (because they are handling read/write).
	def CreateNoteFile(self,name:str, contents:bytes = None)->ENote|None:
		print(f'{DEBUG_PREFIX} Library.CreateNote')
		file:Gio.File = self.file.get_child(name)
		note:ENote|None = self.GetNoteByFile(file)
		if note is not None: # note already exists
			return None
		note = ENote(file)
		note.create(contents)
		self._signal_note_added.emit(note)
		return note
	
	def CreateUniqueNote(self, base_name:str, dot_extension:str='.txt', contents:bytes = None)->ENote:
		file_num:int = 0
		file_name:str = f'{base_name}{dot_extension}'
		file:Gio.File = self.file.get_child(file_name)
		while (file.query_exists()):
			file_num = file_num + 1
			file_name = f'{base_name} {file_num}{dot_extension}'
			file = self.file.get_child(file_name)
		note = ENote(file)
		note.create(contents)
		self._signal_note_added.emit(note)
		return note
	
	def CreateFromTemplate(self, template:ETemplate, name:str=None, unique_base_name:str=None)->ENote:
		data = template.generate_contents(self.metadata) # the content produced from the template and mapping
		note:ENote = None
		if name is not None:
			note = self.CreateNoteFile(name=name,contents=data)
		elif unique_base_name is not None:
			note = self.CreateUniqueNote(base_name=unique_base_name,contents=data)
			if note.exists():
				print(f'{DEBUG_PREFIX} note already exists... cannot create from template. setting note=None')
				note = None
		# TODO
		# elif template.supports_unique_names():
		# 	note = self.CreateUniqueNote...
		# elif template.has_name():
		#	note = self.CreateNoteFile...
		else:
			note = self.CreateUniqueNote('Unnamed note',contents=data)
		
		if note is None:
			print(f'{DEBUG_PREFIX} CreateFromTemplate, note is None')
			return
		return note