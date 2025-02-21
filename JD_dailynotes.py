DEBUG_PREFIX=r'JD_DEBUG '
from JD_yaml_dialog import *;
import gi
gi.require_version('PeasGtk', '1.0')
from gi.repository import PeasGtk
#gi.require_version('Xed', '3.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import Gio
from gi.repository import GLib
from os import getenv # to get users home directory? May not be needed if we just make the path in the config?
from typing import List
import yaml

# look for xed-ui.xml in the xed proj
menubar_ui_string = """<ui>
	<menubar name="MenuBar">
		<menu name="ToolsMenu" action="Tools">
			<placeholder name="ToolsOps_2">
				<menuitem name="JDPlugin" action="JDPlugin_SpawnDialog_Action"/>
				<menuitem name="JDPluginToolOp3" action="JDPlugin_SearchYaml_Action"/>
			</placeholder>
		</menu>
	</menubar>
</ui>"""

class JDPlugin(GObject.Object, Xed.WindowActivatable, PeasGtk.Configurable): #maybe make into ViewActivatable? not like we care about the window
	__gtype_name__ = "JDPlugin"

	window = GObject.property(type=Xed.Window)

	def __init__(self):
		GObject.Object.__init__(self)
		print(f"{DEBUG_PREFIX}plugin init");
		self.user_home_dir = getenv("HOME");
		print(f'{DEBUG_PREFIX} INIT: user_home_dir: {self.user_home_dir}');
		self.search_str = '';

	def do_activate(self): #from WindowActivatable
		print(f"{DEBUG_PREFIX}plugin created for {self.window}")
		self._insert_menu()
	
	def do_deactivate(self): #from WindowActivatable
		print(f"{DEBUG_PREFIX}plugin stopped for {self.window}")
		self._remove_menu()
		self._action_group = None

	def do_update_state(self): #from WindowActivatable
		# window has been updated, such as active tab changed
		print(f"{DEBUG_PREFIX}plugin update for {self.window}")
		self._action_group.set_sensitive(self.window.get_active_document() != None)

	def do_create_configure_widget(self): # from PeasGtk.Configurable
		widget_vbox = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		# --------------
		row_notes_dir = Gtk.Box(spacing=6,orientation=Gtk.Orientation.HORIZONTAL)
		notes_dir_file_browser = Gtk.Label(label="TODO") # spawn a text entry with a button for FileChooserDialog? 
		# ------
		row_notes_dir.pack_start(Gtk.Label(label="notes_dir"),True,True,0)
		row_notes_dir.pack_start(notes_dir_file_browser,True,True,0)
		# --------------
		row_file_regex = Gtk.Box(spacing=6,orientation=Gtk.Orientation.HORIZONTAL)
		file_regex_entry = Gtk.Entry()
		# ------
		row_file_regex.pack_start(Gtk.Label(label="the regex string used to determine what files to check the yaml of"),True,True,0)
		row_file_regex.pack_start(file_regex_entry,True,True,0)
		# --------------
		widget_vbox.pack_start(row_notes_dir,True,True,0)
		widget_vbox.pack_start(row_file_regex,True,True,0)
		# --------------
		# save a config in the users config dir... unless there is a better place.
		return widget_vbox;

	#install menu items
	def _insert_menu(self):
		manager = self.window.get_ui_manager()
		self._action_group = Gtk.ActionGroup("JDPluginActions")
		self._action_group.add_actions(
			[
				("JDPlugin_SpawnDialog_Action",None, _("Set YAML substring match"),
				None, _("choose the substring to look for when parsing notes"),
				self.DO_spawn_dialog),
				("JDPlugin_SearchYaml_Action",None,_("Search YAML"),
	 			None, _("Opens yaml files matching the set substring"), self.DO_SearchNotes),
			])
		manager.insert_action_group(self._action_group, -1)
		self._ui_id = manager.add_ui_from_string(menubar_ui_string)
	
 	#remove installed menu items
	def _remove_menu(self):
		manager=self.window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def DO_spawn_dialog(self,action):
		win = JDPlugin_Dialog_1(self.search_str, self.dialog_callback)
		win.show();

	def dialog_callback(self, text):
		print(f'{DEBUG_PREFIX} dialog_callback received: {text}')
		self.search_str = text;

	def DO_SearchNotes(self,action):
		search = self.search_str
		# The what we want to know about the file.
		# Overview of attributes https://docs.gtk.org/gio/file-attributes.html
		# All attributes https://stuff.mit.edu/afs/sipb/project/barnowl/share/gtk-doc/html/gio/gio-GFileAttribute.html
		search_attributes = ",".join([
			r'standard::name',
			r'standard::content-type',
			r'standard::type',
			r'standard::size',
			r'time::modified',
			r'access::can_read',
		]);
		# TODO: configureable
		notes_directory = Gio.File.new_for_path(f'{self.user_home_dir}/Documents/Notes');
		#! Gio.FileEnumerator
		notes = notes_directory.enumerate_children(
			search_attributes,
			Gio.FileQueryInfoFlags.NONE, # https://lazka.github.io/pgi-docs/Gio-2.0/flags.html#Gio.FileQueryInfoFlags
			None)
		#! fileinfo in 
		print(f'{DEBUG_PREFIX} typeof notes {type(notes)}')
		for note in notes:
			# maybe make a plugin based around the idea:
			# - creates notes formatted with datefrmstr, like %Y-%m-%d
			# - create markdown files
			# - allow search by yaml, just go through every file no bullshit no databse maybe a cache tho
			# - given a search open a bunch of files.. or maybe make a tab?
			print(f'{DEBUG_PREFIX}NOTE: {note.get_name()}',end='')
			if note.get_file_type() == Gio.FileType.DIRECTORY:
				print(f'| DIRECTORY');
			elif note.get_file_type() == Gio.FileType.REGULAR:
				print(f'| FILE')
				PrintFileInfo(note);
				# ValueError: Pointer arguments are restricted to integers, capsules, and None. See: https://bugzilla.gnome.org/show_bug.cgi?id=683599
				# TODO check if this really leaks memory or if they die with the note obj / garbage collector
				# GLib.free(modification_datetime_string)
				note_file = notes_directory.get_child(note.get_name())
				if ProcessFile(self.search_str, note_file):
					self.window.create_tab_from_location(note_file,None,0,0,True);
			else: print("")
		#! TODO docs say to unref, but.... maybe handlded by whatevers doing the binding? I need to find out7
		#! RuntimeException
		# GObject.Object.unref(notes);
		# --------
		# file_bf4 = Gio.File.new_for_path(f'{self.user_home_dir}/Desktop/bf4-eanote.txt')
		# self.window.create_tab_from_location(
		# 	file_bf4, None,
		# 	0,0,True)
		return

def GetFileAttributeData(file_attributes, attribute_key):
	(has_value, file_attribute_type, value_pp, file_attribute_status)\
		= file_attributes.get_attribute_data(attribute_key)
	if (has_value == False)\
		or (file_attribute_type is None)\
		or (value_pp is None)\
		or (file_attribute_status is None):
		return (None, None);
	print(f'{DEBUG_PREFIX} value type (enum): {file_attribute_type}')
	print(f'{DEBUG_PREFIX} status(enum): {file_attribute_status}')
	#  TODO check status invalid
	print(f'{DEBUG_PREFIX} typeof value {type(value_pp)}');
	return (value_pp, file_attribute_type);
		
def PrintFileInfo(file:Gio.FileInfo):
	name = file.get_name()
	file_type:Gio.FileType = file.get_file_type() #https://lazka.github.io/pgi-docs/Gio-2.0/enums.html#Gio.FileType
	modification_datetime_str = file.get_modification_date_time().format_iso8601() # TODO configureable datetime format
	size:int = file.get_size()
	can_read:bool = file.get_attribute_boolean(r'access::can_read')
	content_type:str = file.get_content_type()
	
	print(f'{DEBUG_PREFIX} list {file.list_attributes(None)}')
	print(f'{DEBUG_PREFIX} Name {name}')
	print(f'{DEBUG_PREFIX} Type {file_type}')
	print(f'{DEBUG_PREFIX} Time Modified (iso8601) {modification_datetime_str}')
	print(f'{DEBUG_PREFIX} Size {size} bytes')
	print(f'{DEBUG_PREFIX} can_read {can_read}')
	if (content_type is not None):
		print(f'{DEBUG_PREFIX} content_type {content_type}')
		print(f'{DEBUG_PREFIX} content type seen!')
	
# TODO parse yaml, checkout other python project to see how I went about it.
def ProcessFile(search_str, file:Gio.File) -> bool: # true-> yaml matched!
	found_match:bool = False;
	array_request_len = 64 # See TODO 8
	
	# Gio.FileInputStream
	localFileInputStream = file.read() # retrieve first three chatacters (if type is not 'md', if it is an 'md', might as well make a greedy grab)

	byte_array:GLib.Bytes = localFileInputStream.read_bytes(array_request_len);
	if byte_array is None: return

	condition:bool = byte_array is not None and byte_array.get_size() > 0
	if (condition == False): return

	array:bytes = byte_array.get_data();
	yaml_array:bytes|None = None;
	if (array.startswith(b'---') == False): # TODO handle encoding cases. I imagine this would not work with mandarin text. might come out as '- - - ' in ascii
		print(f'{DEBUG_PREFIX} not yaml {array}')
		return
	print(f'{DEBUG_PREFIX} count {array.count(b'---')} {array}')
	if (array.count(b'---') > 1):
		print(f'{DEBUG_PREFIX} yaml start and end found in first grab')
		yaml_array = array[:array.rfind(b'---')];
		print(f'{DEBUG_PREFIX} array:{array}')
		# TODO find second --- and split the starray (TODO 7)
	else:
		all_bytes:List[bytes] = []
		all_bytes.append(array);
		# TODO YAML
		while(True):
			# TODO read a maximum number of bytes to prevent us from accidentally reading malformed and large files
			byte_array = localFileInputStream.read_bytes(array_request_len);
			if byte_array is None or byte_array.get_size() == 0:
				break;
			array:bytes = byte_array.get_data();
			all_bytes.append(array)
			print(f'{DEBUG_PREFIX} ADD LINE: {array} | find rv: {array.find(b'---')}')
			if (array.find(b'---') > 0): break;
		yaml_array = b''.join(all_bytes)
		yaml_array = yaml_array[:yaml_array.rfind(b'---')]
	
	print(f'{DEBUG_PREFIX} yaml_array:{yaml_array}')
	if yaml_array is not None:
		# TODO try-except here. we are a bit lazy after the while loop and kinda just make a yaml_array by
		# reading the file until EOF. 
		loaded_yaml = yaml.safe_load(yaml_array)
		print(f'{DEBUG_PREFIX} yaml type: {type(loaded_yaml)}\nYAML:\t{loaded_yaml}')
		# JDPlugin_Dialog_WithText('tmpname',loaded_yaml.__str__())
		if len(search_str)>1 and yaml_array.find(bytearray(search_str, encoding='utf-8')) != -1:
			print(f'{DEBUG_PREFIX} substring matched!\nsearch:{search_str}\nyaml:{yaml_array}')
			found_match = True

	localFileInputStream.close();
	return found_match

# EXTERNAL DOCS
# E1 - PyGObject / 'gi': https://amolenaar.pages.gitlab.gnome.org/pygobject-docs/
# E2 - Gio 2.0: https://lazka.github.io/pgi-docs/Gio-2.0/mapping.html
# E3 - Gio 2.0 (official): https://docs.gtk.org/gio/index.html?q=file_enumerate_#enums
# E4 - Gdk3.0: https://docs.gtk.org/gdk3/
# E5 - Python bytes objects: https://docs.python.org/3/library/stdtypes.html#bytes-objects
# E6 - PyYaml: https://pyyaml.org/wiki/PyYAMLDocumentation

# GUIDES
# G1 - Gedit python plugin how to: https://wiki.gnome.org/Apps/Gedit/PythonPluginHowTo
# G2 - How to write plugins for gedit: https://theawless.github.io/How-to-write-plugins-for-gedit/
# G3 - getting a file: https://stackoverflow.com/questions/60109241/how-to-get-icon-for-a-file-using-gio-and-python3
# G4 - PyGObject Asynchronous programming guide (callbacks/asyncio): https://pygobject.gnome.org/guide/asynchronous.html#asynchronous-programming-with-callbacks
# G5 - Where can I find the Python bindings for GIO's GSocket?: https://stackoverflow.com/questions/4677807/where-can-i-find-the-python-bindings-for-gios-gsocket
# G6 - GIO tutorial: File operations: https://sjohannes.wordpress.com/2009/10/10/gio-tutorial-file-operations/#comment-58
# G7 - Tutorial for Gedit3 https://wiki.gnome.org/Apps/Gedit/PythonPluginHowTo
# G8 ! Python Gtk3 Tutorial (BEST RESOURCE) https://python-gtk-3-tutorial.readthedocs.io/en/latest/index.html

# OTHER
# O1 - libyaml (C): https://github.com/yaml/libyaml/

# BUILDING
# Plugins must be placed in:
# ~/.local/share/xed/plugins
# then gdb xed; run

# TODOs (indexed by written order, not priority)
# TODO 1 [ ] rewrite in C (once we get to a comfortable point. Or deep dive into how performance is affected by using the python loader)
# TODO 2 [ ] keep track of yaml we have already seen in some searchable datastruct
# TODO 3 [ ] Provide key-value pairs, possibly with regex to let users wildcard match for some value
# TODO 4 [x] popup dialogue box with search bar
# TODO 5 [ ] Show results in the file browser on the left (maybe or own list instead of the one provided by the ifle browser plugin)
# TODO 6 [ ] asynchronous file searching + support for cancelling. (See G4 and process_files method)
# TODO 7 [ ] (bug) when reading yaml, we read the byte arrays and search for the substring b'---'; however,
#		we do not cover the edge case of the substring being split between subsequent reads. e.g., read 1 ends in "\n--"
#		read 2 begins with "-\n".
# TODO 8 [ ] When processing yaml, make the bytes_read configureable by the user? Maybe they're running on a device with very little ram
#		or they know better than us about  how much data they wish to read at once..
# TODO 9 [ ] Configureable regex for filenames. If non provided, just accept all files. Otherwise, compile a regex string and just check that a match exists.