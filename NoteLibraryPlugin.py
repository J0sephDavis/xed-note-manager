DEBUG_PREFIX='NLP_DEBUG'
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import PeasGtk
from NLP_yaml_dialog import JDPlugin_Dialog_1
from Entities.NLP_EntityNote import ENote
from NLP_Config import NLPConfig
from NLP_PrivateData import PrivateData
from Panels.NLP_PanelManager import NLP_SidePanelManager

# look for xed-ui.xml in the xed proj
menubar_ui_string = """<ui>
	<menubar name="MenuBar">
		<menu name="ToolsMenu" action="Tools">
			<placeholder name="ToolsOps_2">
				<menuitem name="NLPlugin" action="NLPlugin_SpawnDialog_Action"/>
				<menuitem name="NLPluginToolOp3" action="NLPlugin_SearchYaml_Action"/>
				<menuitem name="Create Daily Note" action="NLPlugin_Create_DailyNote"/>
			</placeholder>
		</menu>
	</menubar>
</ui>"""

class NoteLibraryPlugin(GObject.Object, Xed.WindowActivatable, PeasGtk.Configurable): #maybe make into ViewActivatable? not like we care about the window
	__gtype_name__ = "NLPlugin"
	window = GObject.property(type=Xed.Window)
	PluginPrivate = PrivateData()
	def __init__(self):
		print(f'{DEBUG_PREFIX} __init__ NLPlugin')
		self.search_str = 'name' # TOBE deprecated
		GObject.Object.__init__(self)
		self.pluginConfig = NLPConfig()

	# def do_update_state(self):
	# 	print(f'{DEBUG_PREFIX} window:{self.window}')

	def __del__(self):
		print(f'{DEBUG_PREFIX}----- __del__ ---')
		self.PluginPrivate = None
		self.panel_manager = None

	def do_activate(self): #from WindowActivatable
		self.views_handles = {}
		self._insert_menu()
		# Side Panel
		self.panel_manager = NLP_SidePanelManager(self.window, self.DailyNoteRoutine)
		print(f'{DEBUG_PREFIX}\tpanel_manager: {self.panel_manager}')
		self.panel_manager.addTab(internal_name='main', display_name='Libraries', icon_name='folder')
		# window signals (TODO disconnect)
		self.window.connect('tab-added', self.tab_added)
		self.window.connect('tab-removed', self.tab_removed)
		print(f"{DEBUG_PREFIX} plugin created for {self.window}")

	def tab_added(self, window, tab):
		self.views_handles[tab] = tab.get_view().connect("populate-popup", self.view_populate_popup)

	def tab_removed(self, window, tab):
		if tab not in self.views_handles:
			return
		view = tab.get_view()
		view.disconnect(self.views_handles[tab])	
		del self.views_handles[tab]

	def view_populate_popup(self, view:Xed.View, popup:Gtk.Menu):
		print(f'{DEBUG_PREFIX} Plugin PopupMenu')
		sep = Gtk.SeparatorMenuItem()
		sep.show()
		popup.append(sep)

		debugItem = Gtk.MenuItem(label='DEBUG test')
		debugItem.connect('activate', self.DEBUG_MenuItemActivated)
		debugItem.show()
		popup.append(debugItem)

		dailyNoteItem = Gtk.MenuItem(label='Create Daily Note')
		dailyNoteItem.connect('activate',self.DailyNoteRoutine)
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
		self.panel_manager.deactivate()
		
	def do_create_configure_widget(self): # from PeasGtk.Configurable
		return self.pluginConfig.do_create_configure_widget();

	#install menu items
	def _insert_menu(self):
		manager = self.window.get_ui_manager()
		self._action_group = Gtk.ActionGroup("NLPluginActions")
		self._action_group.add_actions(
			[
				("NLPlugin_SpawnDialog_Action",None, _("Set YAML substring match"), # type: ignore
				None, _("choose the substring to look for when parsing notes"), # type: ignore
				self.DO_spawn_dialog),
				# --
				("NLPlugin_SearchYaml_Action",None,_("Search YAML"), # type: ignore
	 			None, _("Opens yaml files matching the set substring"), self.DO_SearchNotes), # type: ignore
				# --
				("NLPlugin_Create_DailyNote", None, _("Create Daily Note"), # type: ignore
	 			None, _("Creates (or opens) todays daily note"), self.DailyNoteRoutine), # type: ignore
			])
		manager.insert_action_group(self._action_group, -1)
		self._ui_id = manager.add_ui_from_string(menubar_ui_string)

 	#remove installed menu items
	def _remove_menu(self):
		manager=self.window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	# requests a daily note to be created
	# request the panel current side pane with the note to be focussed
	# opens the note in a new tab
	def DailyNoteRoutine(self,*args) -> ENote:
		note:ENote = self.PluginPrivate.CreateDailyNote()
		self.panel_manager.handle_note_focus_request(note)
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

def SearchNoteYaml(search_str, note:ENote) -> bool:
	print(f'{DEBUG_PREFIX} processing note: {note.filename}')
	yaml = note.get_yaml()
	if yaml is None:
		print(f'{DEBUG_PREFIX} note contains NO yaml')
		return False
	yaml_str = yaml.__str__()
	print(f'{DEBUG_PREFIX} note yaml: {yaml_str}')
	return yaml_str.find(search_str) >= 0;