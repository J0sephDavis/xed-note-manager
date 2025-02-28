from JD_dailynotes import DEBUG_PREFIX
from JD__entities import JD_EntLibrary, JD_EntNote
from typing import List
import sys
import weakref
from gi.repository import GObject

class EntityManager(GObject.Object): # 
# ------------------------------ life ------------------------
	def __init__(self):
		super().__init__()
		self.libraries:List[JD_EntLibrary] = []
		self.notes_weak:List[JD_EntNote] = []

		self.subscribers_library_removed = [] # try weak refs here. no sense in keeping an object in existence because it has a callback attached.
		self.subscribers_library_added = []

	def deactivate(self):
		print(f'{DEBUG_PREFIX} EntTracker Deactivate ----------------')
		self.subscribers_library_removed.clear()
		self.subscribers_library_added.clear()
		self.libraries.clear()
		self.notes_weak.clear()
# ------------------------------ signals -------------------------------------
	@GObject.Signal(name='library-added', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_library_added(self_entManager, library:JD_EntLibrary):
		print(f'{DEBUG_PREFIX} EntityManager SIGNAL - library-added')

	@GObject.Signal(name='library-removed', flags=GObject.SignalFlags.RUN_LAST, arg_types=(GObject.TYPE_PYOBJECT,))
	def signal_library_removed(self_entManager, library:JD_EntLibrary):
		print(f'{DEBUG_PREFIX} EntityManager SIGNAL - library-removed')
# ------------------------------ properties -------------------------------------
	def GetLibraries(self): return self.libraries
	def GetNotes(self): return self.notes_weak
	def AddLibraries(self, library_paths:List[str]):
		# this is called during JDPlugin.on_activate()
		# the config class exists prior to the entity tracker, thus the callbacks
		# do not exist to handle the added libraries.
		for path in library_paths:
			self.libraryAddedCallback(path)
# ------------------------------ callbacks -------------------------------------
	def libraryAddedCallback(self, library_path:str):
		print(f'{DEBUG_PREFIX} libraryAddedCallback: {library_path}')
		library = JD_EntLibrary(library_path)
		self.libraries.append(library)
		self.signal_library_added.emit(library)

	def libraryRemovedCallback(self, library_path:str):
		print(f'{DEBUG_PREFIX} libraryRemovedCallback: {library_path}')
		removal:List[JD_EntLibrary] = [] #self.libraries.filter(lambda library: library.path == library_path)
		for library in self.libraries:
			if (library.path == library_path):
				removal.append(library)
		print(f'{DEBUG_PREFIX} REMOVAL[]: {removal}')
		for library in removal:
			self.libraries.remove(library)
			self.signal_library_removed.emit(library)
			# print(f'{DEBUG_PREFIX} refcount of library({library.path}): {sys.getrefcount(library)}')