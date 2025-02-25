DEBUG_PREFIX=r'JD_DEBUG '
import gi
gi.require_version('PeasGtk', '1.0')
from gi.repository import PeasGtk
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import GLib
from os import getenv # to get users home directory? May not be needed if we just make the path in the config?

from JD_yaml_dialog import *
from JD__entities import *
from JD__main_config import JDPluginConfig
from JD_sidepanel import *
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
		print(f"{DEBUG_PREFIX}plugin init")
		GObject.Object.__init__(self)
		
		self.user_home_dir = getenv(r'HOME')

		self.search_str = 'name'
		user_config_dir = getenv(r'XDG_CONFIG_HOME')
		if (user_config_dir is None): user_config_dir = f'{self.user_home_dir}/.config/'
		self.pluginConfig = JDPluginConfig(user_config_dir)
		self.libraries:List[JD_EntLibrary] = []
		print(f'{DEBUG_PREFIX} INIT: user_home_dir: {self.user_home_dir}')


	def do_activate(self): #from WindowActivatable
		self._insert_menu()

		self.panel_manager = JDSidePanelManager(self.window.get_side_panel())
		
		self.main_tab = JDPanelTab(self.window)
		self.panel_manager.addTab(self.main_tab)
		
		for library_path in self.pluginConfig.GetLibraries():
			print(f'{DEBUG_PREFIX} library_path: {library_path}')
			library =  JD_EntLibrary(library_path)
			self.main_tab.addLibrary(library) # TODO this will become for library in config.libraries addLibrary(lib).
			self.libraries.append(library)

		self.pluginConfig.SubscribeLibraryAdded(self.config_LibraryAdded)
		self.pluginConfig.SubscribeLibraryRemoved(self.config_LibraryRemoved)
		print(f"{DEBUG_PREFIX}plugin created for {self.window}")

	def config_LibraryAdded(self,library_path:str):
		print(f'{DEBUG_PREFIX} (event) LIBRARY ADDED. {library_path}')
		self.main_tab.addLibrary(JD_EntLibrary(library_path))

	def config_LibraryRemoved(self,library_path:str):
		print(f'{DEBUG_PREFIX} (event) LIBRARY REMOVED. {library_path}')
		self.main_tab.removeLibrary(library_path)

	def do_deactivate(self): #from WindowActivatable
		print(f"{DEBUG_PREFIX}plugin stopped for {self.window}")
		print(f'{DEBUG_PREFIX} TODO: remove side panel') # TODO remove side panel
		self._remove_menu()
		self._action_group = None

	def do_update_state(self): #from WindowActivatable
		# window has been updated, such as active tab changed
		print(f"{DEBUG_PREFIX}plugin update for {self.window}")
		# self._action_group.set_sensitive(self.window.get_active_document() != None)

	def do_create_configure_widget(self): # from PeasGtk.Configurable
		return self.pluginConfig.createConfigureWidget();

	#install menu items
	def _insert_menu(self):
		manager = self.window.get_ui_manager()
		self._action_group = Gtk.ActionGroup("JDPluginActions")
		self._action_group.add_actions(
			[
				("JDPlugin_SpawnDialog_Action",None, _("Set YAML substring match"), # type: ignore
				None, _("choose the substring to look for when parsing notes"), # type: ignore
				self.DO_spawn_dialog),
				("JDPlugin_SearchYaml_Action",None,_("Search YAML"), # type: ignore
	 			None, _("Opens yaml files matching the set substring"), self.DO_SearchNotes), # type: ignore
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
		for note in self.library.GetNotes():
			print(f'{DEBUG_PREFIX} NOTE: {note.filename}')
			if SearchNoteYaml(search, note):
				# JDPlugin_FileInformation_Window(note)
				note.open_in_new_tab(self.window)

def SearchNoteYaml(search_str, note:JD_EntNote) -> bool:
	print(f'{DEBUG_PREFIX} processing note: {note.filename}')
	yaml = note.get_yaml()
	if yaml is None:
		print(f'{DEBUG_PREFIX} note contains NO yaml')
		return False
	yaml_str = yaml.__str__()
	print(f'{DEBUG_PREFIX} note yaml: {yaml_str}')
	return yaml_str.find(search_str) >= 0;

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
# TODO 10 [ ] Save user configuration......