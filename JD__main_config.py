from JD__utils import *
from gi.repository import Gtk
from os import getenv;
from typing import Dict, List

class JDPluginConfig():
	already_init=False
	# libraries:List[str] = []
	def __new__(self):
		print(f'{DEBUG_PREFIX} JDPluginConfig __new__  ======================')
		if not hasattr(self,'instance'):
			print(f'{DEBUG_PREFIX} creating new instance')
			self.instance = super().__new__(self)
		print(f'{DEBUG_PREFIX} returning existing instance')
		return self.instance


	def __init__(self):
		print(f'{DEBUG_PREFIX} JDPluginConfig.__init__')
		if (self.already_init):
			print(f'{DEBUG_PREFIX} JDPluginConfig INIT TRAP')
			return
		self.already_init = True
		user_home_dir = getenv('HOME')
		user_config_dir = getenv('XDG_CONFIG_HOME')
		if (user_config_dir is None):
			user_config_dir = f'{user_home_dir}/.config/'

		self.config_file_path:str = user_config_dir + 'xed_JDplugin.conf'

		self.library_added_callbacks = []
		self.library_removed_callbacks = []

		self.__yaml:Dict = None
		self._loadConfig()

	def GetLibraries(self) -> List[str]:
		if 'notes_directories' in self.__yaml:
			return self.__yaml['notes_directories']
		return []
	def GetDailyNotesPath(self)->str:
		if 'daily_notes_path' in self.__yaml:
			return self.__yaml['daily_notes_path']
		return None

	def _loadConfig(self):
		assert self.__yaml is None, "JDPluginConfig:_loadConfig self.__yaml is not None."

		print(f'{DEBUG_PREFIX} Loading configuration file ({self.config_file_path})')
		file:Gio.File = getFileFromPath(self.config_file_path)
		if (file.query_exists()): self.__yaml = readYAML(self.config_file_path)
		# ---
		if (self.__yaml is None): self.__yaml = {}
		print(f'{DEBUG_PREFIX} config:  {type(self.__yaml)}\n{self.__yaml}')

	def saveConfig(self,save_button, libraryPath_GtkTextView,daily_note_text_entry):
		old_libraries = self.GetLibraries()
		libraries:List[str] = []
		self.__yaml['notes_directories'] = libraries
		assert libraries is not old_libraries, "libraries is old_libraries. yaml[notes_dir] should have been replaced with a new list."
		# --- Get the libraries from the widget's buffer
		buffer = libraryPath_GtkTextView.get_buffer()
		buff_text:List[str] = buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter(),False).splitlines()
		# -- Notify subscribers about new libraries
		for line in buff_text:
			libraries.append(line) # TODO check whether they are valid directories? Maybe warn or silent fail. It's not always a big deal, especially if you use removable drives.
			if line not in old_libraries:
				self.EmitLibraryAdded(line)
		# -- Notify subscribers about libraries which have been removed
		for removed_library in filter(lambda old_lib: old_lib not in libraries, old_libraries):
			self.EmitLibraryRemoved(removed_library)
		# --- Daily Note Text Entry
		daily_notes_path = daily_note_text_entry.get_text()
		old_daily_notes_path = self.GetDailyNotesPath()
		print(f'{DEBUG_PREFIX} old:{old_daily_notes_path} new:{daily_notes_path}')
		if (old_daily_notes_path is not None or old_daily_notes_path != ''):
			#  There WAS an old path, and it is not equal to the new path
			if (old_daily_notes_path != daily_notes_path):
				self.EmitLibraryRemoved(old_daily_notes_path)
				if (daily_notes_path is not None and daily_notes_path != ''):
					self.EmitLibraryAdded(daily_notes_path)
					print(f'{DEBUG_PREFIX} saveConfig, daily notes directory: {daily_notes_path}')
					self.__yaml['daily_notes_path'] = daily_notes_path
		elif (daily_notes_path is not None and daily_notes_path != ''): # creating a path when one previously did not exist
			self.EmitLibraryAdded(daily_notes_path)
			self.__yaml['daily_notes_path'] = daily_notes_path
		else:
			self.__yaml['daily_notes_path'] = None
		print(f'{DEBUG_PREFIX} saveConfig, daily notes directory: {self.GetDailyNotesPath()}')

		# --- Write to File
		file:Gio.File = getFileFromPath(self.config_file_path)
		if (file.query_exists()): # despite using the FileCreateFlags.REPLACE_DESTINATION, an error is stillthrown if the file exists...
			file.delete()
		outputStream:Gio.FileOutputStream = file.create(Gio.FileCreateFlags.REPLACE_DESTINATION, None)
		yaml_bytes = bytearray(yaml.dump(self.__yaml, explicit_start=True,explicit_end=False) + '---', encoding='utf-8')
		outputStream.write_all(yaml_bytes)
		outputStream.close()

	def createConfigureWidget(self):
		print(f'{DEBUG_PREFIX} JDpluginConfig createConfigureWidget')
		widget = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		# -- Daily note text entry
		text = None
		if 'daily_notes_path' in self.__yaml:
			text =  self.__yaml['daily_notes_path']
		if text is None:
			text = ''
		daily_note_text_entry = Gtk.Entry(text=text)
		widget.pack_start(Gtk.Label(label="Daily notes folder"), False,False,0)
		widget.pack_start(daily_note_text_entry, True,True,0)
		# -- Note directory text view
		libraryPaths_GtkTextView = Gtk.TextView()
		text = None
		if 'notes_directories' in self.__yaml:
			text = self.__yaml['notes_directories']
			if text is not None:
				text = '\n'.join(text)
		if text is None:
			text = ''
		libraryPaths_GtkTextView.get_buffer().set_text(text)
		widget.pack_start(Gtk.Label(label="notes_dir"),False,False,0)
		widget.pack_start(libraryPaths_GtkTextView,True,True,0) # TOD request more size!
		# -- Save Button
		save_button = Gtk.Button.new_with_label("Save")
		save_button.connect("clicked",self.saveConfig, libraryPaths_GtkTextView, daily_note_text_entry)
		widget.pack_start(save_button,False,False,0)
		# --------------
		widget.show_all()
		return widget

	def SubscribeLibraryAdded(self, callback): 
		print(f'{DEBUG_PREFIX} JDPluginConfig SUBSCRIBER LIBRARY ADDED {callback}')
		self.library_added_callbacks.append(callback)
		print(f'{DEBUG_PREFIX} JDPluginConfig {self.library_added_callbacks}')

	def SubscribeLibraryRemoved(self, callback):
		print(f'{DEBUG_PREFIX} JDPluginConfig SUBSCRIBER LIBRARY REMOVED {callback}')
		self.library_removed_callbacks.append(callback)
		print(f'{DEBUG_PREFIX} JDPluginConfig {self.library_removed_callbacks}')

	def EmitLibraryAdded(self, library_path:str):
		print(f'{DEBUG_PREFIX} JDPluginConfig ANNOUNCE LIBRARY ADDED: {library_path}\n{self.library_added_callbacks}')
		for cb in self.library_added_callbacks:
			cb(library_path)

	def EmitLibraryRemoved(self, library_path:str):
		print(f'{DEBUG_PREFIX} JDPluginConfig ANNOUNCE LIBRARY REMOVED: {library_path}\n{self.library_removed_callbacks}')
		for cb in self.library_removed_callbacks:
			cb(library_path)