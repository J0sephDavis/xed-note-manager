from JD__utils import *
import os
from gi.repository import Xed
from gi.repository import GLib
class JDPluginConfig():
	def __init__(self, config_file_path:str):
		self.user_home_dir = os.getenv('HOME')
		self.path = config_file_path + 'xed_JDplugin.conf'
		self.yaml = None
		self._loadConfig()

	def GetLibraryPath(self): # TODO support multiple paths
		# return f'{self.user_home_dir}/Documents/Notes'
		return self.yaml['notes_directory']

	def _loadConfig(self):
		print(f'{DEBUG_PREFIX} Loading configuration file ({self.path})')
		file:Gio.File = getFileFromPath(self.path)
		if (file.query_exists()): self.yaml = readYAML(self.path)
		if self.yaml is not None:
			print(f'{DEBUG_PREFIX} config yaml found: {self.yaml}')
			return
		print(f'{DEBUG_PREFIX} config does not exist, yet.')
		self.yaml = {
			"notes_directory" : f'{self.user_home_dir}/Documents/Notes',
		}

	def saveConfig(self):
		print(f'{DEBUG_PREFIX} saveConfig:\n{self.yaml}\n{self.yaml.__str__()}')
		file:Gio.File = getFileFromPath(self.path)
		if (file.query_exists()):
			file.delete()
		outputStream:Gio.FileOutputStream = file.create(Gio.FileCreateFlags.REPLACE_DESTINATION, None)
		yaml_bytes = bytearray(yaml.dump(self.yaml, explicit_start=True,explicit_end=False) + '---', encoding='utf-8')
		outputStream.write_all(yaml_bytes)
		outputStream.close()