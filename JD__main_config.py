DEBUG_PREFIX=r'JD_DEBUG '
from typing import List
from JD__utils import *
import re
import os
from gi.repository import Xed
from gi.repository import GLib
class JDPluginConfig():
	def __init__(self, config_file_path:str):
		self.user_home_dir = os.getenv('HOME')
		self.path = config_file_path + 'xed_JDplugin.conf'
		self.yaml = None
		self._loadConfig()

	def GetLibraryPath(self): # TODO support multiple paths
		# return f'{self.user_home_dir}/Documents/Notes'
		return self.yaml['notes_directory']

	def _loadConfig(self):
		print(f'{DEBUG_PREFIX} Loading configuration file ({self.path})')
		file:Gio.File = getFileFromPath(self.path)
		if (file.query_exists()): self.yaml = readYAML(self.path)
		if self.yaml is not None:
			print(f'{DEBUG_PREFIX} config yaml found: {self.yaml}')
			return
		print(f'{DEBUG_PREFIX} config does not exist, yet.')
		self.yaml = {
			"notes_directory" : f'{self.user_home_dir}/Documents/Notes',
		}

	def saveConfig(self):
		print(f'{DEBUG_PREFIX} saveConfig:\n{self.yaml}\n{self.yaml.__str__()}')
		file:Gio.File = getFileFromPath(self.path)
		if (file.query_exists()):
			file.delete()
		outputStream:Gio.FileOutputStream = file.create(Gio.FileCreateFlags.REPLACE_DESTINATION, None)
		yaml_bytes = bytearray(yaml.dump(self.yaml, explicit_start=True,explicit_end=False) + '---', encoding='utf-8')
		outputStream.write_all(yaml_bytes)
		outputStream.close()

class JD_EntBase():
	def __init__(self, fileInfo:Gio.FileInfo):
		self.filename = fileInfo.get_name()
	# 	self.SortName = filename
	# 	self.DisplayName = filename

	# def SetDisplayName(self, name:str):
	# 	self.DisplayName = name
	
	# def SetSortName(self, name:str):
	# 	self.SortName = name

class JD_EntNote(JD_EntBase):
	def __init__(self, parent_dir:str, fileInfo:Gio.FileInfo):
		super().__init__(fileInfo)
		self.path = f'{parent_dir}/{fileInfo.get_name()}'
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
			Gio.FileQueryInfoFlags.NONE, # https://lazka.github.io/pgi-docs/Gio-2.0/flags.html#Gio.FileQueryInfoFlags # TODO configurable
			None
		)
		for note in notes:
			# PrintFileAttributeData(note)
			# TODO name filters (self.regex_filter & class.regex_filter)
			if note.get_file_type() == Gio.FileType.REGULAR: # TODO reevaluate filter on FileType
				self.notes.append(JD_EntNote(self.path, note))

	# def setFilter(self, regex_str):
	# 	self.regex_filter = re.compile(regex_str)