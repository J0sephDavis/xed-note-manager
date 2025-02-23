from JD__utils import *
from gi.repository import Gtk
import os

class JDPluginConfig():
	user_home_dir = os.getenv('HOME')

	def __init__(self, config_file_path:str):
		print(f'{DEBUG_PREFIX} JDPluginConfig.__init__')
		self.path = config_file_path + 'xed_JDplugin.conf'
		self.widget = None
		self.yaml = None
		self.libraries = []
		self._loadConfig()

	def GetLibraries(self) -> List[str]: # TODO support multiple paths
		return self.yaml['notes_directories']

	def _loadConfig(self):
		self.yaml = None
		print(f'{DEBUG_PREFIX} Loading configuration file ({self.path})')
		file:Gio.File = getFileFromPath(self.path)
		if (file.query_exists()): self.yaml = readYAML(self.path)
		if self.yaml is None:
			print(f'{DEBUG_PREFIX} config does not exist. Creating')
			self.yaml = {
			"notes_directories" : [f'{self.user_home_dir}/Documents/Notes'],
			}
			return
		# ---
		print(f'{DEBUG_PREFIX} config:  {type(self.yaml)}\n{self.yaml}')
		# ---
		# self.libraries = []
		for dir in self.yaml["notes_directories"]:
			print(f'{DEBUG_PREFIX} loadConfig, append dir: {dir}')
			self.libraries.append(dir)

	def saveConfig(self,action=None):
		print(f'{DEBUG_PREFIX} saveConfig:\n{self.yaml}')
		file:Gio.File = getFileFromPath(self.path)
		if (file.query_exists()):
			file.delete()
		buffer = self.libraryPaths_GtkTextView.get_buffer()
		buff_text:List[str] = buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter(),False).splitlines()
		self.libraries = []
		for line in buff_text:
			print(f'{DEBUG_PREFIX} saveConfig, append dir {line}')
			self.libraries.append(line)
		self.yaml['notes_directories'] = self.libraries
		outputStream:Gio.FileOutputStream = file.create(Gio.FileCreateFlags.REPLACE_DESTINATION, None)
		yaml_bytes = bytearray(yaml.dump(self.yaml, explicit_start=True,explicit_end=False) + '---', encoding='utf-8')
		outputStream.write_all(yaml_bytes)
		outputStream.close()

	def _createWidget(self):
		self.widget = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		# --------------
		# row_notes_dir = Gtk.Box(spacing=6,orientation=Gtk.Orientation.HORIZONTAL)
		# notes_dir_path_label = Gtk.Label(label=self.GetLibraryPath())
		self.libraryPaths_GtkTextView = Gtk.TextView()
		text = self.yaml['notes_directories']
		if text is None:
			text = ''
		else:
			text = '\n'.join(text)
		self.libraryPaths_GtkTextView.get_buffer().set_text(text)
		# ------
		self.widget.pack_start(Gtk.Label(label="notes_dir"),True,True,0)
		# row_notes_dir.pack_start(notes_dir_path_label,True,True,0)
		self.widget.pack_start(self.libraryPaths_GtkTextView,True,True,0) # TOD request more size!
		# --------------
		row_file_regex = Gtk.Box(spacing=6,orientation=Gtk.Orientation.HORIZONTAL)
		file_regex_entry = Gtk.Entry()
		# ------
		row_file_regex.pack_start(Gtk.Label(label="the regex string used to determine what files to check the yaml of"),True,True,0)
		row_file_regex.pack_start(file_regex_entry,True,True,0)
		# --------------
		# TODO save on close instead of with this button? the close button comes default... maybe get signal of widget being destroyed?
		save_button = Gtk.Button.new_with_label("Save")
		save_button.connect("clicked",self.saveConfig)
		# --------------
		# widget_vbox.pack_start(row_notes_dir,True,True,0)
		self.widget.pack_start(row_file_regex,True,True,0)
		self.widget.pack_start(save_button,True,True,0)
		# --------------
		# TODO button with callback connected to saveConfig

	def createConfigureWidget(self):
		if self.widget is None: self._createWidget()
		return self.widget