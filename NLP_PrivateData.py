import gi
from gi.repository import GObject

from Entities.NLP_EntityManager import EntityManager
from Entities.NLP_EntityLibrary import ELibrary
from Entities.NLP_EntityNote import ENote
from NLP_Config import NLPConfig
from datetime import datetime
from NoteLibraryPlugin import DEBUG_PREFIX
from typing import List

class PrivateData():
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls,'_self'):
			cls._self = super(PrivateData, cls).__new__(cls)
		return cls._self
	
	init_trap:bool = False
	def __init__(self):
		print(f'{DEBUG_PREFIX} __init__ PrivateData')
		if (self.init_trap): return
		self.init_trap = True
		self.pluginConfig = NLPConfig()
		# Entity Tracking
		self.entTracker = EntityManager()

		libraries:List[str] = self.pluginConfig.GetLibraries()
		if (len(libraries) > 0):
			self.entTracker.AddLibraries(self.pluginConfig.GetLibraries())
		daily_notes = self.pluginConfig.GetDailyNotesPath()
		if (daily_notes is not None):
			self.entTracker.DailyNotesPathUpdated(None, self.pluginConfig.GetDailyNotesPath())

		self.pluginConfig.connect('library-path-added',self.entTracker.AddLibraryPath)
		self.pluginConfig.connect('library-path-removed',self.entTracker.RemoveLibraryPath)
		self.pluginConfig.connect('daily-notes-path-updated', self.entTracker.DailyNotesPathUpdated)

	def __del__(self):
		self.entTracker.deactivate()
		self.entTracker = None