from NoteLibraryPlugin import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib
from gi.repository import Gio
from gi.repository import Gtk
from typing import List,Tuple,Callable
import yaml
import subprocess
# import chardet
__read_buffer_length = 64

# returns a GFile that does not exist
# if default_file_name is 'note', then the files 
def new_unique_file(directory:Gio.File, default_file_name:str) -> Gio.File:
	num_file:int = 0
	file_name:str = None
	_file:Gio.File = directory.get_child(default_file_name)
	while(_file.query_exists() == True):
		if (num_file == 0):
			file_name = default_file_name
		else:
			file_name = f'{default_file_name} {num_file}'
		_file = directory.get_child(file_name)
		num_file = num_file + 1
	print(f'{DEBUG_PREFIX} new_unique_file: {_file.get_basename()}')
	return _file

def GetFileContents(file:Gio.File)->bytes|None:#Tuple[bytes,str]|None: #contents, encoding
	is_load_successful,contents,etag_out = file.load_contents()
	if (not is_load_successful):
		return None
	# if (len(contents) > 256):
	# 	enc_inf = chardet.detect(contents[:256])
	# else:
	# 	enc_inf = chardet.detect(contents)
	# print(f'{DEBUG_PREFIX} getFileContents encoding={enc_inf.get('encoding')}')
	return contents #, enc_inf.get('encoding','Unknown')

def __getLine(inputStream:Gio.FileInputStream) -> bytes|None:
	byte_array:GLib.Bytes|None;
	try:
		byte_array = inputStream.read_bytes(__read_buffer_length)
	except GLib.Error as error: # byte_array is set None on failure
		print(f'{DEBUG_PREFIX} utils.__getLine err code: {error.code}\nmsg: {error.message}')
	
	if (byte_array is None or byte_array.get_size() == 0):
		return None
	else:
		return byte_array.get_data()
	

def readYAML(file_path:str) -> object: # TODO perform YAML safe load here
	#file:Gio.File = getFile(file)
	file:Gio.File = getFileFromPath(file_path)
	if file is None:
		print(f'{DEBUG_PREFIX} readYAML 404, file not found... {file_path}')
		return None
	print(f'{DEBUG_PREFIX} readYAML from: {file_path}')
	yaml_buff:str|None = None
	
	inputStream = file.read()
	#---- file stream opened
	data:bytes|None = __getLine(inputStream)
	if data is None: # empty file
		return None
	if data.startswith(b'---') == False: # file does not begin with yaml frontmatter.
		# this could be improved, whitespace would prevent this from being a proper doc
		# ? Strip leading whitespace / use a regex match to make it clear (^\s*---)
		print(f'{DEBUG_PREFIX} file does not begin with yaml.')
		return None
	
	if data.count(b'---') > 1:
		print(f'{DEBUG_PREFIX} yaml complete in first draw. Tenho 天和')
		yaml_buff = data[:data.rfind(b'---')]
	else: # continue reading yaml to complete
		buffer:List[bytes] = [data]
		valid:bool = False;
		while (True):
			data = __getLine(inputStream)
			if data is None:
				print(f'{DEBUG_PREFIX} EOF')
				# break, but leave valid as False.
				# so that we may close the filestream
				break;
			buffer.append(data)
			print(f'{DEBUG_PREFIX} buffer.append: {data}')
			if data.find(b'---') >= 0:
				valid = True
				break
		if (valid):
			yaml_buff:bytes = b''.join(buffer)
			yaml_buff = yaml_buff[:yaml_buff.rfind(b'---')] # remove all text at the end of the doc. (including the second ---)
			print(f'{DEBUG_PREFIX} yaml buffered: {yaml_buff}')
	#---- file stream closed
	inputStream.close()
	if yaml_buff is None:
		print(f'{DEBUG_PREFIX} no yaml_str.')
		return None
	return yaml.safe_load(yaml_buff)

def getFileFromPath(file_path:str) -> Gio.File:
	return Gio.File.new_for_path(file_path)

def OpenPathInFileExplorer(path:str):
	subprocess.call(["xdg-open",path])

def menu_separator():
	return Gtk.SeparatorMenuItem()

def new_menu_item(label:str, handler:Callable, *args):
	item = Gtk.MenuItem.new_with_label(label)
	item.connect('activate', handler, *args)
	return item