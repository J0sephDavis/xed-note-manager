from JD__utils import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import Gdk

from JD_PluginPrivateData import JDPluginPrivate
from Panels.JD_sidepanel import JDPanelTab
from JD_EntManager import EntityManager
from JD__entities import JD_EntLibrary, JD_EntNote, JD_EntBase

from typing import List,Tuple

class JDSidePanelManager():
	def __init__(self, window:Xed.Window):
		self.PluginPrivateData = JDPluginPrivate()
		self.side_panel = window.get_side_panel()
		self.window = window
		self.entityTracker:EntityManager = self.PluginPrivateData.entTracker
		self.panels:List[JDPanelTab] = []
		print(f'{DEBUG_PREFIX} SidePanelManager __init__')

	def addTab(self, internal_name:str, display_name:str, icon_name:str):
		print(f'{DEBUG_PREFIX} SidePanelManager addTab')
		panel_tab = JDPanelTab(internal_name=internal_name, display_name=display_name, icon_name=icon_name,window=self.window)
		self.side_panel.add_item(panel_tab.GetWidget(),panel_tab.display_name,panel_tab.icon_name)
		self.entityTracker.connect('library-added', panel_tab.OnLibraryAdded)
		self.entityTracker.connect('library-removed', panel_tab.OnLibraryRemoved)
		for library in self.entityTracker.GetLibraries():
			panel_tab.OnLibraryAdded(None, library)
		self.panels.append(panel_tab)

	def getTab(self, tab_internal_name:str) -> JDPanelTab|None:
		for panel in self.panels:
			if panel.internal_name == tab_internal_name:
				return panel
		return None

	def deactivate(self):
		print(f'{DEBUG_PREFIX} JDSidePanelManager.deactivate()')
		for panel in self.panels:
			print(f'{DEBUG_PREFIX} removing panel {panel.internal_name}')
			self.side_panel.remove_item(panel.GetWidget())
			panel.treeView.get_model().clear() # Is this necessary? Or will it be destroyed when we clear the widget.
			panel.widget_container = None # TODO move this code into panel.deactivate() method
		self.panels.clear()
		self.side_panel = None

	# def handle_note_focus_request(self, caller, note:JD_EntNote):
	# 	# 1. Find the first panel tab which contains this note.
	# 	for panel in self.panels:
	# 		notes = panel.
	# 	# 2. Focus the tab
	# 	# 3. Unfold the library
	# 	# 4. Focus the note

	# 	# - Open the note in a new tab
	# 	pass