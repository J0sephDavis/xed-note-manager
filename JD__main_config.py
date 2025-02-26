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

	def _loadConfig(self):
		assert self.__yaml is None, "JDPluginConfig:_loadConfig self.__yaml is not None."

		print(f'{DEBUG_PREFIX} Loading configuration file ({self.config_file_path})')
		file:Gio.File = getFileFromPath(self.config_file_path)
		if (file.query_exists()): self.__yaml = readYAML(self.config_file_path)
		if self.__yaml is None:
			print(f'{DEBUG_PREFIX} config does not exist. Creating')
			self.__yaml = {
			"notes_directories" : [f'{getenv('HOME')}/Documents/Notes'],
			}
			return
		# ---
		print(f'{DEBUG_PREFIX} config:  {type(self.__yaml)}\n{self.__yaml}')

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

	def saveConfig(self,save_button, libraryPath_GtkTextView):
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
		# --------------
		# row_notes_dir = Gtk.Box(spacing=6,orientation=Gtk.Orientation.HORIZONTAL)
		# notes_dir_path_label = Gtk.Label(label=self.GetLibraryPath())
		libraryPaths_GtkTextView = Gtk.TextView()
		text = self.__yaml['notes_directories']
		if text is None:
			text = ''
		else:
			text = '\n'.join(text)
		libraryPaths_GtkTextView.get_buffer().set_text(text)
		# ------
		widget.pack_start(Gtk.Label(label="notes_dir"),True,True,0)
		# row_notes_dir.pack_start(notes_dir_path_label,True,True,0)
		widget.pack_start(libraryPaths_GtkTextView,True,True,0) # TOD request more size!
		# --------------
		row_file_regex = Gtk.Box(spacing=6,orientation=Gtk.Orientation.HORIZONTAL)
		file_regex_entry = Gtk.Entry()
		# ------
		row_file_regex.pack_start(Gtk.Label(label="the regex string used to determine what files to check the yaml of"),True,True,0)
		row_file_regex.pack_start(file_regex_entry,True,True,0)
		# --------------
		# TODO save on close instead of with this button? the close button comes default... maybe get signal of widget being destroyed?
		save_button = Gtk.Button.new_with_label("Save")
		save_button.connect("clicked",self.saveConfig, libraryPaths_GtkTextView)
		# --------------
		# widget_vbox.pack_start(row_notes_dir,True,True,0)
		widget.pack_start(row_file_regex,True,True,0)
		widget.pack_start(save_button,True,True,0)
		# --------------
		widget.show_all()
		return widget