from gi.repository import Gio;
from JD__utils import *
class JD_EntBase(): # TODO: use as the base  for the TreeModel entries? With a getModel() command?
	# File
	# File Name
	# Display Name
	# Sort Name?

	def __init__(self, file:Gio.File):
		self.file = file;
	
	def getFilename(self): return self.file.get_basename()


class JD_EntNote(JD_EntBase):
	def __init__(self, parent_dir:str, fileInfo:Gio.FileInfo):
		self.fileInfo = fileInfo
		self.path = f'{parent_dir}/{fileInfo.get_name()}'

		super().__init__(getFileFromPath(self.path))
		
		self.file_read:bool = False # True ONLY if readYAML has been called already.
		self.fileInfo = fileInfo
		self.__yaml = None# = readYAML(fileInfo.get_name())
		
	def open_in_new_tab(self, window): # window is the main Xed window
		window.create_tab_from_location(
			getFileFromPath(self.path),
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
	# static & instance regex filters. Then should they be A||B, A&&B, A+B, or even A-B
	# regex_filter = None # TODO set from JDPluginConfig
	def __init__(self, library_path:str):
		self.path = library_path
		print(f'{DEBUG_PREFIX} library_path: {self.path}')
		library:Gio.File = getFileFromPath(self.path) # TODO try-except to get the dir
		super().__init__(file=library)
		self.notes:List[JD_EntNote] = []
		self._get_notes()
		# self.regex_filter = None

	def GetNotes(self):
		# TODO accept a function that accepts a JD_EntNode and returns bool. Returns a list of notes compared by that function
		return self.notes;

	def _get_notes(self):
		library:Gio.File = getFileFromPath(self.path) # TODO try-except to get the dir
		# PrintFileAttributeData(library)
		# Overview of attributes https://docs.gtk.org/gio/file-attributes.html
		# All attributes https://stuff.mit.edu/afs/sipb/project/barnowl/share/gtk-doc/html/gio/gio-GFileAttribute.html
		search_attributes = ",".join([
			r'standard::name',
			r'standard::content-type',
			r'standard::type',
			r'standard::size',
			r'time::modified',
			r'access::can_read',
		]);
		
		notes = library.enumerate_children(
			search_attributes,
			# https://lazka.github.io/pgi-docs/Gio-2.0/flags.html#Gio.FileQueryInfoFlags # TODO configurable
			Gio.FileQueryInfoFlags.NONE,
			None
		)
		for note in notes:
			# TODO name filters (self.regex_filter & class.regex_filter)
			if note.get_file_type() == Gio.FileType.REGULAR: # TODO reevaluate filter on FileType
				self.notes.append(JD_EntNote(self.path, note))

	# def setFilter(self, regex_str):
	# 	self.regex_filter = re.compile(regex_str)