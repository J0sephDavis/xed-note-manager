from NLP_Utils import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import Gdk

from NLP_PrivateData import PrivateData
from Panels.NLP_PanelTab import PanelTab
from Entities.NLP_EntityManager import EntityManager
from Entities.NLP_EntityLibrary import ELibrary
from Entities.NLP_EntityNote import ENote
from Entities.NLP_EntityBase import EBase

from typing import List,Tuple

class NLP_SidePanelManager():
	def __init__(self, window:Xed.Window, delegate_DailyNoteRoutine):
		self.PluginPrivateData = PrivateData()
		self.side_panel = window.get_side_panel()
		self.window = window
		self.delegate_DailyNoteRoutine = delegate_DailyNoteRoutine
		self.entityTracker:EntityManager = self.PluginPrivateData.entTracker
		self.panels:List[PanelTab] = []

	def addTab(self, internal_name:str, display_name:str, icon_name:str):
		panel_tab = PanelTab(
			internal_name=internal_name,
			display_name=display_name,
			icon_name=icon_name,
			window=self.window,
			ent_tracker=self.entityTracker,
			delegate_DailyNoteRoutine=self.delegate_DailyNoteRoutine)
		self.side_panel.add_item(panel_tab.GetWidget(),panel_tab.display_name,panel_tab.icon_name)
		for library in self.entityTracker.GetLibraries():
			panel_tab.OnLibraryAdded(None, library)
		self.panels.append(panel_tab)

	def getTab(self, tab_internal_name:str) -> PanelTab|None:
		for panel in self.panels:
			if panel.internal_name == tab_internal_name:
				return panel
		return None

	def deactivate(self):
		print(f'{DEBUG_PREFIX} JDSidePanelManager.deactivate()')
		for panel in self.panels:
			print(f'{DEBUG_PREFIX} removing panel {panel.internal_name}')
			self.side_panel.remove_item(panel.GetWidget())
			panel.do_deactivate()
		self.panels.clear()
		self.side_panel = None

	def handle_note_focus_request(self, note:ENote):
		print(f'{DEBUG_PREFIX} handle_note_focus_request')
		panel = None
		note_path:Gtk.TreePath = None
		for panel in self.panels:
			note_path = panel.GetNote(note)
			if (note_path is not None):
				break
		if (note_path is None):
			print(f'{DEBUG_PREFIX} handle_note_focus_request no notes found')
			return
		self.side_panel.activate_item(panel) # switches to the tab
		panel.FocusNote(note_path)