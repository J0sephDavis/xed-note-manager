from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
from Entities.NLP_EntityBase import EBase
from NLP_Utils import GetFileContents
from typing import Callable, List,Tuple,Dict
import re
from enum import IntEnum,auto
class FileNameEnum(IntEnum):
	MAKE_UNIQUE_NAME = auto()
	PRESET_NAME = auto()
	STARTSWITH_NAME = auto() # similar to static, but the name must start with the templated value. Nice for daily notes
# from Entities.NLP_EntityLibrary import ELibrary
from NLP_Template import NLP_Template
class ETemplate(EBase): # TODO check if the file has been updated (maybe this is handled by ELibrary who monitors the dir)
	default_unique_filename:bytes = b'Note'
	unique_filename_delimieter:bytes = b'#'
	normal_filename_delimieter:bytes = b'@'
	startswith_filename_delimieter:bytes = b'^'

	template_extension='.template'
	template_extension_len=len(template_extension)
	
	def __init__(self, file:Gio.File):
		super().__init__(file,None)
		self.template:NLP_Template = None
		fname = file.get_basename()
		index = fname.rfind(self.template_extension)
		if index == 0:
			fname = 'default' # TODO this seems... wrong. eventually someone will make default.template and they will conflict
		else:
			fname = fname[:index]
		self.identifier:str = fname
		if self.identifier == '': self.identifier = fname

		print(self.identifier)
		self.t_body:bytes = None
		self.t_name:Tuple[FileNameEnum,bytes]|None = None # file_name_type:FileNameEnum, the template string:bytes # converted from bytes to string in generate_filename()
		self.load_file()

	# did it succeed?
	def load_file(self, force_reload:bool=False) ->bool:
		if (self.template is not None and force_reload == False): return # if the template is set and force reload is false. ret
		success:bool
		contents:bytes
		etag:str
		success, contents, etag = self.file.load_contents()
		if not success:
			print(f'{DEBUG_PREFIX} ETemplate.load_file success=False')
			return success
		
		file_name_type:FileNameEnum;
		if contents.startswith(self.unique_filename_delimieter):
			file_name_type = FileNameEnum.MAKE_UNIQUE_NAME
		elif contents.startswith(self.startswith_filename_delimieter):
			file_name_type = FileNameEnum.STARTSWITH_NAME
		elif contents.startswith(self.normal_filename_delimieter):
			file_name_type = FileNameEnum.PRESET_NAME
		else:
			file_name_type = None
		
		separator=b'\n' # maybe make these class variable? If we ever run into problems with LF vs CRLF this could be useful. Unsure how Gio.File implements load_contents given the difference...
		l_sep = len(separator)
		if (file_name_type is not None):
			first_break = contents.find(separator)
			self.t_body = contents[first_break+l_sep:]
			self.t_name = (file_name_type, contents[1:first_break])# starts at [1:.] to skip the delimiter
		else: # no name provided.
			self.t_name = (FileNameEnum.MAKE_UNIQUE_NAME,self.default_unique_filename)
			self.t_body = contents
		
		return success
	
	def generate_filename(self, value_map:Dict)->Tuple[FileNameEnum,str,str]: # returns whether the name can be made unique or not. file name, file extension
		# It might be worth using chardet on the contents to determine the correct conversion of the filename. TODO test with some asian characters
		bname:bytes = self.t_name[1]
		if self.t_name is None: raise RuntimeError('ETemplate.t_name is none, something went wrong.')
		
		if self.template is None: self.template = NLP_Template(bname)
		else: self.template.template = bname

		fname:bytes = self.template.custom_safe_substitute(value_map)
		last_dot = fname.rfind(b'.')
		extension:str = fname[last_dot:].decode('utf-8')
		name:str = fname[:last_dot].decode('utf-8')
		print(f'name: {name}')
		print(f'ext: {extension}')
		return self.t_name[0],name,extension
		# return self.t_name[0],fname.decode('utf-8') # TODO chardet to handle utf-16 / chinese
	
	def generate_contents(self,value_map:(Dict[bytes,				# key value must be a byte string
							# in addition to these, you could probably add
							# ones that do not conform. So long as their
							# KEY will never be matched. such as $sjdklf
							# Then, that data can be accessed within the
							# complex replacement
							bytes | 								# simple replacement
							Callable[[re.Match[bytes]],bytes]] |	# function replacement, func(bytes)->bytes
							Callable[[re.Match,dict],bytes])		# complex replacement, func(bytes,mapping)->bytes
						)->bytes:
		if (self.template is None): self.template = NLP_Template(self.t_body)
		else: self.template.template = self.t_body

		return self.template.custom_safe_substitute(value_map)