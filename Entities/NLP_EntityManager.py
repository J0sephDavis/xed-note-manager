from NoteLibraryPlugin import DEBUG_PREFIX
from Entities.NLP_EntityLibrary import ELibrary
from typing import List
from gi.repository import GObject, GLib

class EntityManager(GObject.Object): # 
# ------------------------------ life ------------------------
	def __init__(self):
		super().__init__()
		self.daily_notes_library:ELibrary = None
		self.libraries:List[ELibrary] = []

		self.subscribers_library_removed = [] # try weak refs here. no sense in keeping an object in existence because it has a callback attached.
		self.subscribers_library_added = []

	def deactivate(self):
		print(f'{DEBUG_PREFIX} EntTracker Deactivate ----------------')
		self.daily_notes_library:ELibrary = None
		self.subscribers_library_removed.clear()
		self.subscribers_library_added.clear()
		self.libraries.clear()
# ------------------------------ signals -------------------------------------
	@GObject.Signal(name='library-added', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_library_added(self_entManager, library:ELibrary):
		print(f'{DEBUG_PREFIX} EntityManager SIGNAL - library-added {library.get_path()}')

	@GObject.Signal(name='library-removed', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_library_removed(self_entManager, library:ELibrary):
		print(f'{DEBUG_PREFIX} EntityManager SIGNAL - library-removed {library.get_path()}')

	@GObject.Signal(name='daily-notes-library-updated', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_daily_notes_library_updated(self_entManager, library:ELibrary|None):
		print(f'{DEBUG_PREFIX} EntityManager SIGNAL - daily-notes-library-updated {library.get_path()}')
# ------------------------------ properties -------------------------------------
	def GetLibraries(self): return self.libraries
	def AddLibraries(self, library_paths:List[str]):
		for path in library_paths:
			self.AddLibraryPath(None, path)

	def DailyNotesPathUpdated(self,caller,library_path:str|None): # connected in PrivateData.__init__
		if (library_path is None or library_path.isspace()):
			if (self.daily_notes_library is None): return
			self.daily_notes_library = None
		else:
			if (self.daily_notes_library is not None\
	   				and self.daily_notes_library.get_path() == library_path):
					return
			# TODO try-except creation of library
			self.daily_notes_library = ELibrary.from_path(library_path, True)
		self.signal_daily_notes_library_updated.emit(self.daily_notes_library)
# ------------------------------ callbacks -------------------------------------
	def AddLibraryPath(self, caller, library_path:str):
		print(f'{DEBUG_PREFIX} AddLibraryPath: {library_path}')
		try:
			library = ELibrary.from_path(path=library_path)
		except GLib.Error as e:
			print(f'EXCEPTION EntityManager::AddLibrary({library_path}) GLib.Error({e.code}): {e.message}')
			return
		self.libraries.append(library)
		self.signal_library_added.emit(library)

	def RemoveLibraryPath(self, caller, library_path:str):
		print(f'{DEBUG_PREFIX} RemoveLibraryPath: {library_path}')
		removal:List[ELibrary] = [] #self.libraries.filter(lambda library: library.path == library_path)
		for library in self.libraries:
			if (library.get_path() == library_path):
				removal.append(library)
		print(f'{DEBUG_PREFIX} REMOVAL[]: {removal}')
		for library in removal:
			self.libraries.remove(library)
			self.signal_library_removed.emit(library)