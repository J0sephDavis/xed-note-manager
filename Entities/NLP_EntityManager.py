from NoteLibraryPlugin import DEBUG_PREFIX
from Entities.NLP_EntityLibrary import ELibrary
from typing import List
from gi.repository import GObject, GLib

class EntityManager(GObject.Object): # 
# ------------------------------ life ------------------------
	def __init__(self):
		super().__init__()
		self.libraries:List[ELibrary] = []

		self.subscribers_library_removed = [] # try weak refs here. no sense in keeping an object in existence because it has a callback attached.
		self.subscribers_library_added = []

	def deactivate(self):
		print(f'{DEBUG_PREFIX} EntTracker Deactivate ----------------')
		self.subscribers_library_removed.clear()
		self.subscribers_library_added.clear()
		self.libraries.clear()
# ------------------------------ signals -------------------------------------
	@GObject.Signal(name='library-added', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_library_added(self_entManager, library:ELibrary):
		print(f'{DEBUG_PREFIX} EntityManager SIGNAL - library-added {library.path}')

	@GObject.Signal(name='library-removed', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_library_removed(self_entManager, library:ELibrary):
		print(f'{DEBUG_PREFIX} EntityManager SIGNAL - library-removed {library.path}')
# ------------------------------ properties -------------------------------------
	def GetLibraries(self): return self.libraries
	def AddLibraries(self, library_paths:List[str]):
		# this is called during JDPlugin.on_activate()
		# the config class exists prior to the entity tracker, thus the callbacks
		# do not exist to handle the added libraries.
		for path in library_paths:
			self.AddLibraryPath(None, path)
# ------------------------------ callbacks -------------------------------------
	def AddLibraryPath(self, caller, library_path:str):
		print(f'{DEBUG_PREFIX} AddLibrary: {library_path}')
		try:
			library = ELibrary(library_path)
		except GLib.Error as e:
			print(f'EXCEPTION EntityManager::AddLibrary({library_path}) GLib.Error({e.code}): {e.message}')
			return
		self.libraries.append(library)
		self.signal_library_added.emit(library)

	def RemoveLibraryPath(self, caller, library_path:str):
		print(f'{DEBUG_PREFIX} libraryRemovedCallback: {library_path}')
		removal:List[ELibrary] = [] #self.libraries.filter(lambda library: library.path == library_path)
		for library in self.libraries:
			if (library.path == library_path):
				removal.append(library)
		print(f'{DEBUG_PREFIX} REMOVAL[]: {removal}')
		for library in removal:
			self.libraries.remove(library)
			self.signal_library_removed.emit(library)