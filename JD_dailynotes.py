DEBUG_PREFIX=r'JD_DEBUG '
import gi
gi.require_version('PeasGtk', '1.0')
gi.require_version('Xed', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import PeasGtk
from gi.repository import Xed

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
				<menuitem name="Create Daily Note" action="JDPlugin_Create_DailyNote"/>
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

	def do_update_state(self):
		print(f'{DEBUG_PREFIX} window:{self.window}')

	def do_activate(self): #from WindowActivatable
		self.views_handles = {}
		self._insert_menu()
		self.PluginPrivate = JDPluginPriv()
		# Side Panel
		self.panel_manager = JDSidePanelManager(self.window)
		print(f'{DEBUG_PREFIX}\tpanel_manager: {self.panel_manager}')
		self.panel_manager.addTab(internal_name='main', display_name='Libraries', icon_name='folder')
		# window signals
		self.window.connect('tab-added', self.tab_added)
		self.window.connect('tab-removed', self.tab_removed)
		print(f"{DEBUG_PREFIX} plugin created for {self.window}")

	def tab_added(self, window, tab):
		print(f'{DEBUG_PREFIX} TAB_ADDED\twindow:{window}\ttab:{tab}')
		self.views_handles[tab] = tab.get_view().connect("populate-popup", self.view_populate_popup)
		print(f'{DEBUG_PREFIX} {type(self.views_handles)} current_views: {self.views_handles}')

	def tab_removed(self, window, tab):
		print(f'{DEBUG_PREFIX} TAB_REMOVED\twindow:{window}\ttab:{tab}')
		view = tab.get_view()
		view.disconnect(self.views_handles[tab])
		del self.views_handles[tab]
		print(f'{DEBUG_PREFIX} {type(self.views_handles)} current_views: {self.views_handles}')

	def view_populate_popup(self, view:Xed.View, popup:Gtk.Menu):
		print(f'{DEBUG_PREFIX} Plugin PopupMenu')
		sep = Gtk.SeparatorMenuItem()
		sep.show()
		popup.append(sep)

		debugItem = Gtk.MenuItem(label='DEBUG test')
		debugItem.connect('activate', self.DEBUG_MenuItemActivated)
		debugItem.show()
		popup.append(debugItem)

		dailyNoteItem = Gtk.MenuItem(label='Create/GOTO Daily Note')
		dailyNoteItem.connect('activate',self.DO_DailyNote)
		dailyNoteItem.show()
		popup.append(dailyNoteItem)
	
	def DEBUG_MenuItemActivated(self, menuItem):
		print(f'----------------------------------------------\n{DEBUG_PREFIX} Current tabs with populate-popup set: ')
		for val in self.views_handles:
			print(f'{DEBUG_PREFIX}\t{val}\t{self.views_handles[val]}')
		print(f'----------------------------------------------')
	

	def do_deactivate(self): #from WindowActivatable
		print(f"{DEBUG_PREFIX}plugin stopped for {self.window}")
		self._remove_menu()
		self._action_group = None
		
	def do_create_configure_widget(self): # from PeasGtk.Configurable
		return self.pluginConfig.do_create_configure_widget();

	#install menu items
	def _insert_menu(self):
		manager = self.window.get_ui_manager()
		self._action_group = Gtk.ActionGroup("JDPluginActions")
		self._action_group.add_actions(
			[
				("JDPlugin_SpawnDialog_Action",None, _("Set YAML substring match"), # type: ignore
				None, _("choose the substring to look for when parsing notes"), # type: ignore
				self.DO_spawn_dialog),
				# --
				("JDPlugin_SearchYaml_Action",None,_("Search YAML"), # type: ignore
	 			None, _("Opens yaml files matching the set substring"), self.DO_SearchNotes), # type: ignore
				# --
				("JDPlugin_Create_DailyNote", None, _("Create a daily note"), # type: ignore
	 			None, _("Creates (or opens) todays daily note"), self.DO_DailyNote), # type: ignore
			])
		manager.insert_action_group(self._action_group, -1)
		self._ui_id = manager.add_ui_from_string(menubar_ui_string)

 	#remove installed menu items
	def _remove_menu(self):
		manager=self.window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def DO_DailyNote(self,*args):
		note = self.PluginPrivate.CreateDailyNote()
		if note is None: return None
		note.open_in_new_tab(self.window)
		return note

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
