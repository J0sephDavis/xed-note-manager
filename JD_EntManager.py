from JD__entities import *
import sys
import weakref
class JD_EntTracker(): # TODO better name
	libraries:List[JD_EntLibrary] = []
	notes_weak:List[JD_EntNote] = []
	discard_pile:List[JD_EntLibrary] = [] # weak refs to every library we have removed. for debugging

	subscribers_library_removed = [] # try weak refs here. no sense in keeping an object in existence because it has a callback attached.
	subscribers_library_added = []

	def __init__(self):
		pass
	
	def deactivate(self):
		print(f'{DEBUG_PREFIX} EntTracker Deactivate ----------------')
		self.subscribers_library_removed.clear()
		self.subscribers_library_added.clear()
		self.libraries.clear()
		self.discard_pile.clear()
		self.notes_weak.clear()
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
		self.announceLibraryAdded(library)

	def libraryRemovedCallback(self, library_path:str):
		print(f'{DEBUG_PREFIX} libraryRemovedCallback: {library_path}')
		removal:List[JD_EntLibrary] = [] #self.libraries.filter(lambda library: library.path == library_path)
		for library in self.libraries:
			if (library.path == library_path):
				removal.append(library)
		print(f'{DEBUG_PREFIX} REMOVAL[]: {removal}')
		for library in removal:
			self.libraries.remove(library)
			self.announceLibraryRemoved(library)
			print(f'{DEBUG_PREFIX} refcount of library({library.path}): {sys.getrefcount(library)}')
			self.discard_pile.append(weakref.ref(library))
# --------------------------------- events ----------------------------------------
	def announceLibraryRemoved(self, library:JD_EntLibrary):
		print(f'{DEBUG_PREFIX} EntTracker announceLibraryRemoved {library.path}\n{self.subscribers_library_removed}')
		for callback in self.subscribers_library_removed:
			callback()(library)
	
	def announceLibraryAdded(self,library:JD_EntLibrary):
		print(f'{DEBUG_PREFIX} EntTracker announceLibraryAdded {library.path}\n {self.subscribers_library_added}')
		for callback in self.subscribers_library_added:
			callback()(library)

	def subscribeLibraryAdded(self, callback): 
		if not callable(callback):
			print(f'{DEBUG_PREFIX} EntTracker subscribeLibraryAdded, callback is not callable.')
			return
		self.subscribers_library_added.append(weakref.WeakMethod(callback))

	def subscribeLibraryRemoved(self, callback): 
		if not callable(callback):
			print(f'{DEBUG_PREFIX} EntTracker subscribeLibraryRemoved, callback is not callable.')
			return
		self.subscribers_library_removed.append(weakref.WeakMethod(callback))