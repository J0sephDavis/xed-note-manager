from NoteLibraryPlugin import DEBUG_PREFIX
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
from Entities.NLP_EntityBase import EBase
from NLP_Utils import GetFileContents
from typing import Callable, List
import re
# from Entities.NLP_EntityLibrary import ELibrary
from NLP_Template import NLP_Template
class ETemplate(EBase): # TODO check if the file has been updated (maybe this is handled by ELibrary who monitors the dir)
	def __init__(self, file:Gio.File):
		super().__init__(file,None)
		self.template:NLP_Template = None

	def load_file(self):
		if (self.template is None):
			self.template = NLP_Template(GetFileContents(self.file))
		return self.template
	
	def generate_filename(self):
		pass
	
	def generate_contents(self,value_map:(dict[bytes,				# key value must be a byte string
							# in addition to these, you could probably add
							# ones that do not conform. So long as their
							# KEY will never be matched. such as $sjdklf
							# Then, that data can be accessed within the
							# complex replacement
							bytes | 								# simple replacement
							Callable[[re.Match[bytes]],bytes]] |	# function replacement, func(bytes)->bytes
							Callable[[re.Match,dict],bytes])		# complex replacement, func(bytes,mapping)->bytes
						)->bytes:
		if (self.template is None): self.load_file()
		return self.template.custom_safe_substitute(value_map)