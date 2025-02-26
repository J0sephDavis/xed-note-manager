DEBUG_PREFIX=r'JD_DEBUG '
import gi
gi.require_version('PeasGtk', '1.0')
from gi.repository import PeasGtk
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed

from JD_yaml_dialog import *
from JD__entities import *
from JD__main_config import JDPluginConfig
from JD_sidepanel import *
from JD_EntManager import JD_EntTracker
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
		print(f'{DEBUG_PREFIX} ------------------ JDPlugin init -----------------')
		self.search_str = 'name' # TOBE deprecated
		GObject.Object.__init__(self)
		self.pluginConfig = JDPluginConfig()


	def do_activate(self): #from WindowActivatable
		# Entity Tracking
		self.entTracker = JD_EntTracker()
		self.entTracker.AddLibraries(self.pluginConfig.GetLibraries())
		self.pluginConfig.SubscribeLibraryAdded(self.entTracker.libraryAddedCallback)
		self.pluginConfig.SubscribeLibraryRemoved(self.entTracker.libraryRemovedCallback)
		# Side Panel
		self.panel_manager = JDSidePanelManager(self.window.get_side_panel(), self.entTracker)
		main_tab = JDPanelTab(internal_name='main', display_name='Libraries', icon_name='folder', window=self.window)
		self.panel_manager.addTab(main_tab)	

		self._insert_menu()
		print(f"{DEBUG_PREFIX}plugin created for {self.window}")

	def do_deactivate(self): #from WindowActivatable
		print(f"{DEBUG_PREFIX}plugin stopped for {self.window}")
		self._remove_menu()
		self._action_group = None
		
		self.panel_manager.deactivate()
		self.panel_manager = None

		self.entTracker.deactivate()
		self.entTracker = None

	def do_update_state(self): #from WindowActivatable
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