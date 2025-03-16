from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import Gio
from NLP_Utils import getFileFromPath, OpenPathInFileExplorer, new_unique_file
from typing import List,Callable,Dict,Tuple
from Entities.NLP_EntityBase import EBase
from Entities.NLP_EntityNote import ENote
from Entities.NLP_EntityTemplate import ETemplate,FileNameEnum
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
						  b'strftime': lambda bstr: str_utf8(datetime.strftime(datetime.now(), bstr.decode('utf-8'))) # what are you doing....
		}
	
	def __get_notes_from_dir(self, no_clobber:bool = True, emit_signals:bool = True):
		add_note:Callable[[ENote],None] = self._signal_note_added.emit if emit_signals else self._signal_note_added
		# ---
		directory_enumerator:Gio.FileEnumerator = self.file.enumerate_children(
			self.search_attributes,
			Gio.FileQueryInfoFlags.NONE,
			None
		)
		# ---
		file_info:Gio.FileInfo
		template_arr:List[Gio.FileInfo] = []
		note_arr:List[Gio.FileInfo] = []
		for file_info in directory_enumerator:
			if file_info.get_file_type() != Gio.FileType.REGULAR: continue
			if file_info.get_name().endswith('.template'):
				template_arr.append(file_info)
			else:
				note_arr.append(file_info)
		
		file:Gio.File
		for file_info in template_arr:
			file = directory_enumerator.get_child(file_info)
			template = ETemplate(file)
			if no_clobber and template in template_arr:
				continue
			self.templates.append(file)

		for file_info in note_arr:
			file = directory_enumerator.get_child(file_info)
			note = ENote(file)
			if no_clobber and note in note_arr:
				continue
			add_note(note)
		
	# Get Notes
	def GetNotes(self)->List[ENote]: return self.notes
	def GetNoteByName(self,name:str)->ENote|None:
		note:ENote|None = None
		for note in self.notes:
			if note.get_filename() == name: break
		return note
	def GetNoteByFile(self,file:Gio.File)->ENote|None:
		for note in self.notes:
			if note.file.equal(file): return note
		return None
	# Get Templates
	def GetTemplates(self)->List[ETemplate]: return self.templates
	def GetTemplateByName(self,name:str)->ETemplate:
		template:ETemplate|None = None
		for template in self.templates:
			if template.get_filename() == name: break # TODO implement an EBase.get_name() for a generic name? for notes it would be the file name. libraries dir name, and templates maybe a user-provided name
		return template
	
	# returns (created_file:bool, note:ENote)
	def CreateNote_StartsWith(self,name:str, extension:str, contents:bytes)->Tuple[bool,ENote]:
		print(f'{DEBUG_PREFIX} CreateNote_StartsWith {name}\t{extension}')
		directory_enumerator:Gio.FileEnumerator = self.file.enumerate_children(
			self.search_attributes,
			Gio.FileQueryInfoFlags.NONE,
			None
		)
		matching_children:List[Gio.FileInfo] = [child for child in directory_enumerator if child.get_name().startswith(name)]
		if len(matching_children) == 0:
			print(f'{DEBUG_PREFIX} No file starting with {name}, creating.')
			return self.CreateNoteFile(
				name=name,
				extension=extension,
				contents=contents
			)
		# File starting with the substring exists already.
		if len(matching_children) > 1: print(f'{DEBUG_PREFIX} CreateNote_StartsWith, multiple files with name already exist..... 0th index will be used regardless.')
		file:Gio.File = directory_enumerator.get_child(matching_children[0])
		# Does it already have an entity?
		note:ENote|None =  self.GetNoteByFile(file)
		if note is None:
			print(f'{DEBUG_PREFIX} There was no ENote with the given name, but the file already existed. So we are adding it to the list')
			note = ENote(file)
			self._signal_note_added.emit(note)
		return (False,note)
				
	# returns (created_file:bool, note:ENote)
	def CreateNoteFile(self,name:str, extension:str, contents:bytes)->Tuple[bool,ENote]:
		file_name = f'{name}{extension}'
		file:Gio.File = self.file.get_child(file_name)
		print(f'{DEBUG_PREFIX} Library.CreateNote {file_name}')
		
		note:ENote|None = self.GetNoteByFile(file)
		if note is not None: # note already exists
			print(f'{DEBUG_PREFIX} note already exists')
			return (False,note)
		
		note = ENote(file)
		if note.exists(): # note already exists in file system. TODO add note to the panel because it should probably be there if it has been seen here
			print(f'{DEBUG_PREFIX} file already exists')
			self._signal_note_added(note) # because it wasn't found in GetNoteByFile
			return (False,note)
		note.create(contents)
		self._signal_note_added.emit(note)
		return (True,note)
	
	# returns (created_file:bool, note:ENote)
	def CreateUniqueNote(self, name:str, extension:str, contents:bytes)->Tuple[bool,ENote]:
		file_num:int = 0
		file_name:str = f'{name}{extension}'
		file:Gio.File = self.file.get_child(file_name)
		while (file.query_exists()):
			file_num = file_num + 1
			file_name = f'{name} {file_num}{extension}'
			file = self.file.get_child(file_name)
		note = ENote(file)
		note.create(contents)
		self._signal_note_added.emit(note)
		return (True,note)
	
	# returns (created_file:bool, note:ENote)
	def CreateFromTemplate(self, template:ETemplate)->Tuple[bool,ENote]:
		name_enum,name,extension = template.generate_filename(self.metadata)
		t_body:bytes = template.generate_contents(self.metadata) # the content produced from the template and mapping

		note:ENote = None
		if name_enum == FileNameEnum.MAKE_UNIQUE_NAME:
			retval = self.CreateUniqueNote(name=name, extension=extension, contents=t_body)
		elif name_enum == FileNameEnum.IMMUTABLE_NAME:
			retval = self.CreateNoteFile(name=name, extension=extension, contents=t_body)
		elif name_enum == FileNameEnum.STARTSWITH_NAME:
			retval = self.CreateNote_StartsWith(name=name, extension=extension ,contents=t_body)

		if retval[1] is None:
			print(f'{DEBUG_PREFIX} WARNING CreateFromTemplate, note is None')
		return retval