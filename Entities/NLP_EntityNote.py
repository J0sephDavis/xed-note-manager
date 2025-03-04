from NoteLibraryPlugin import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
from gi.repository import Xed
from gi.repository import Gio
from NLP_Utils import getFileFromPath, readYAML, OpenPathInFileExplorer
import yaml
from Entities.NLP_EntityBase import EBase

class ENote(EBase):
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