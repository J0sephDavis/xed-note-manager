from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
from Entities.NLP_EntityBase import EBase
from gi.repository import Gio
from NLP_Utils import new_unique_file, GetFileContents
from typing import Callable, List
import re
# from Entities.NLP_EntityLibrary import ELibrary
from NLP_Template import NLP_Template
class ETemplate(EBase):
	def __init__(self, file:Gio.File):
		super().__init__(file,None)
		self.template:NLP_Template = None
		self.data:bytes = None

	def load_file(self):
		if (self.template is None):
			self.template = NLP_Template(GetFileContents(self.file))
		return self.template
	
	# def ChooseFileName(self, library:ELibrary, make_unique:bool):
	# 	pass
	
	def GetContents(self,value_map:dict[bytes,
							# simple replacement
							bytes |\
							#def func(bytes)->bytes
							Callable[[re.Match[bytes]],bytes]] | \
							#def func(bytes,value_map:dict)->bytes
							Callable[[re.Match,dict],bytes]
						)->bytes:
		raise NotImplementedError("GetContents not implemented")
		if self.data is None: 
			self.data = self.template.custom_safe_substitute(value_map)
		return self.data
	
	# make_unique appends a number to the end. e.g, note, note 1, note 2, note 3...
	def save_to_file(self,dir:Gio.File,make_unique:bool):
		raise NotImplementedError("save_to_file not implemented")
		if dir.exists():
			if make_unique == False:
				return False
		# dir.
		
		pass