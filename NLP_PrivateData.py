import gi
from gi.repository import GObject

from Entities.NLP_EntityManager import EntityManager
from NLP_Entities import ELibrary, ENote
from NLP_Config import NLPConfig
from datetime import datetime
from NoteLibraryPlugin import DEBUG_PREFIX

class PrivateData():
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls,'_self'):
			cls._self = super(PrivateData, cls).__new__(cls)
		return cls._self
	
	init_trap:bool = False
	def __init__(self):
		print(f'{DEBUG_PREFIX} __init__ JDPluginPrivate')
		if (self.init_trap): return
		self.init_trap = True
		self.pluginConfig = NLPConfig()
		# Entity Tracking
		self.entTracker = EntityManager()
		self.entTracker.AddLibraries(self.pluginConfig.GetLibraries())
		self.entTracker.AddLibraryPath(None, self.pluginConfig.GetDailyNotesPath())
		self.pluginConfig.connect('library-path-added',self.entTracker.AddLibraryPath)
		self.pluginConfig.connect('library-path-removed',self.entTracker.RemoveLibraryPath)

	def __del__(self):
		self.entTracker.deactivate()
		self.entTracker = None

	def GetDailyNotesLibrary(self) -> ELibrary|None:
		daily_notes_path = self.pluginConfig.GetDailyNotesPath()
		libraries = self.entTracker.GetLibraries()
		for library in libraries:
			if library.path == daily_notes_path:
				return library
		return None
	
	def CreateDailyNote(self) -> ENote:
		lib = self.GetDailyNotesLibrary()
		if lib is None: return None
		date:datetime = datetime.now()
		date_str:str = date.strftime(r'%Y-%m-%d')
		found_note:ENote|None = None
		for note in lib.GetNotes():
			filename = note.get_filename()
			print(f'{filename}')
			if filename.startswith(date_str):
				print(f'NOTE FOUND: {filename}')
				found_note = note
				break
		if (found_note is None):
			found_note = lib.GetCreateNote(f'{date_str} Daily Note.txt') # TODO configurable name
		
		print(f'{DEBUG_PREFIX} CreateDailyNote date_str:{found_note.get_filename()}')
		return found_note