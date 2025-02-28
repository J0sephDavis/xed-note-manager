DEBUG_PREFIX='JD_DEBUG'
import weakref
from JD_EntManager import *
from JD__main_config import *
from datetime import datetime
class JDPluginPriv():
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls,'_self'):
			cls._self = super(JDPluginPriv, cls).__new__(cls)
		return cls._self
	
	init_trap:bool = False
	def __init__(self):
		print(f'{DEBUG_PREFIX} JDPluginData -----------------------------------')
		if (self.init_trap): return
		self.init_trap = True
		self.pluginConfig = JDPluginConfig()
		print(f'{DEBUG_PREFIX}\pluginConfig: {self.pluginConfig}')
		# Entity Tracking
		self.entTracker = JD_EntTracker()
		print(f'{DEBUG_PREFIX}\tentTracker: {self.entTracker}')
		self.entTracker.AddLibraries(self.pluginConfig.GetLibraries())
		self.entTracker.libraryAddedCallback(self.pluginConfig.GetDailyNotesPath())
		self.pluginConfig.SubscribeLibraryAdded(self.entTracker.libraryAddedCallback)
		self.pluginConfig.SubscribeLibraryRemoved(self.entTracker.libraryRemovedCallback)

	def __del__(self):
		self.panel_manager.deactivate()
		self.panel_manager = None
		self.entTracker.deactivate()
		self.entTracker = None

	def GetDailyNotesLibrary(self) -> JD_EntLibrary|None:
		daily_notes_path = self.pluginConfig.GetDailyNotesPath()
		libraries = self.entTracker.GetLibraries()
		for library in libraries:
			if library.path == daily_notes_path:
				return library
		return None
	
	def CreateDailyNote(self) -> JD_EntNote|None:
		lib = self.GetDailyNotesLibrary()
		if lib is None: return None
		
		date:datetime = datetime.now()
		filename = date.strftime(r'%Y-%m-%d Daily Note.md')
		print(f'{DEBUG_PREFIX} create note {filename}')
		note = lib.GetCreateNote(filename)
		return note