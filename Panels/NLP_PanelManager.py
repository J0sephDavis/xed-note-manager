from NLP_Utils import DEBUG_PREFIX
from typing import List,Dict
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import Gdk

from Entities.NLP_EntityNote import ENote
from NLP_PrivateData import PrivateData

from Panels.NLP_LibraryPanelTab import LibraryPanelTab
from Panels.NLP_DailyNotePanel import DailyNotePanel
from Panels.NLP_PanelTabBase import PanelTabBase

class SidePanelManager():
	def __init__(self, window:Xed.Window, delegate_DailyNoteRoutine):
		self.PluginPrivateData = PrivateData()
		self.side_panel = window.get_side_panel()
		self.window = window
		self.delegate_DailyNoteRoutine = delegate_DailyNoteRoutine
		self.panels:List[PanelTabBase] = []

	def addTab(self, tab:PanelTabBase):
		self.side_panel.add_item(tab.GetWidget(),tab.display_name,tab.icon_name)
		self.panels.append(tab)
		self.side_panel.activate_item(tab)

	def getTab(self, tab_internal_name:str) -> LibraryPanelTab|None:
		for panel in self.panels:
			if panel.internal_name == tab_internal_name:
				return panel
		return None

	def removeTab(self,tab_internal_name:str):
		panel = self.getTab(tab_internal_name)
		if panel is not None:
			self.panels.remove(panel)
			self.side_panel.remove_item(panel)
			panel.do_deactivate()

	def deactivate(self):
		print(f'{DEBUG_PREFIX} NLP_PanelManager.deactivate()')
		for panel in self.panels:
			print(f'{DEBUG_PREFIX} removing panel {panel.internal_name}')
			self.side_panel.remove_item(panel.GetWidget())
			panel.do_deactivate()
		self.panels.clear()
		self.side_panel = None

	def handle_note_focus_request(self, note:ENote, daily_note:bool=False):
		print(f'{DEBUG_PREFIX} handle_note_focus_request')
		if (daily_note):
			panel:DailyNotePanel = self.getTab('daily-notes')
			panel.TryFocusNote(note)
			self.side_panel.activate_item(panel) # switches to the tab
		else:
			panel:PanelTabBase = None
			note_path:Gtk.TreePath = None
			for panel in self.panels:
				if (panel.TryFocusNote(note)):
					self.side_panel.activate_item(panel) # switches to the tab
					return
		print(f'{DEBUG_PREFIX} handle_note_focus_request no notes found')