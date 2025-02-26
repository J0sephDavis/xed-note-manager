import gi
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import GLib

from JD__entities import *
from JD__utils import DEBUG_PREFIX
from typing import List
from JD_EntManager import *
# (later)
# - right click menu to choose whether a file shoudl be opened in a new tab, deleted, moved, &c
# - select multiple notes and open/delete/perform some other action on them
# Aesthetic TODO
# - folder and file icons like the filebrowser sidepanel
# common interfaces for side panel tabs
# - getName()
# - getIcon()
# - getWidget()
# - getStore()

def treeStorePrintRow(store,tPath,tIter):
	print('\t' * (tPath.get_depth()-1), store[tIter][:], sep="")

class JDPanelTab(Gtk.TreeView):
	def __init__(self, internal_name:str, display_name:str, icon_name:str, window:Xed.Window):
		super().__init__()
		self.internal_name = internal_name
		self.display_name = display_name
		self.icon_name = icon_name
		print(f'{DEBUG_PREFIX} PanelTab __init__')
		self.widget_container = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)

		treeStore:Gtk.TreeStore = Gtk.TreeStore(str, GObject.TYPE_PYOBJECT)
		self.treeView:Gtk.TreeView = Gtk.TreeView(model=treeStore)
		
		self.treeView.insert_column(
			Gtk.TreeViewColumn(title='name', cell_renderer=Gtk.CellRendererText(),text=0),
			position=-1
		)
		
		# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeView.html#signals
		self.treeView.connect("row-activated", self.handler_row_activated, window)

		remove_item_button = Gtk.Button(label="Remove Selected")
		remove_item_button.connect("clicked", self.handler_remove_selected)
		self.widget_container.pack_start(remove_item_button,False,True,5)
		self.widget_container.pack_start(self.treeView,True,True,0)
		self.widget_container.show_all()

	def GetWidget(self): return self.widget_container;

	def handler_row_activated(self, treeview, path, col, window):
		count_selection = treeview.get_selection().count_selected_rows()
		print(f'{DEBUG_PREFIX} !!!row-ativated:\n\tpath{path}\n\tselection-size:{count_selection}')
		if count_selection > 1: return
		model = treeview.get_model()
		iter:Gtk.TreeIter = model.get_iter(path)
		model[iter][1].open_in_new_tab(window)
	
	def handler_remove_selected(self, button): # this could probably be moved to JDSidePanelManager because it does not need to rely on instance data (which could be passed as args)
		print(f'{DEBUG_PREFIX} handler_remove_selected')
		selection:Gtk.TreeSelection = self.treeView.get_selection()
		selection_mode = selection.get_mode()

		if (selection_mode != Gtk.SelectionMode.SINGLE and selection_mode != Gtk.SelectionMode.BROWSE):
			print(f'{DEBUG_PREFIX} handler_remove_selected get_selected() only supports single selection or browse selection. Use get_selected_rows()\n{selection_mode}')
			return
		
		model,selected_iter = selection.get_selected()
		entry = model[selected_iter]
		if (selected_iter is None):
			print(f'{DEBUG_PREFIX} handler_remove_selected, no entries selected.')
			return
		print(f'{DEBUG_PREFIX} {type(entry)} SELECTED[0] {entry[0]} [1]: {entry[1]}')
		if (type(entry[1]) is JD_EntLibrary):
			print(f'{DEBUG_PREFIX} removing library {entry[0]}')
			self.treeView.get_model().remove(selected_iter)
		else:
			print(f'{DEBUG_PREFIX} selected entry is not a library {entry[0]}, {type(entry[1])}')
			return

	def onLibraryAdded(self,library:JD_EntLibrary): # called by entity tracker
		print(f'{DEBUG_PREFIX} PanelTab addLibrary path:{library.path}')
		node:Gtk.TreeIter = self.treeView.get_model().append(None, [library.getFilename(), library])
		for note in library.notes:
			self.treeView.get_model().append(node, [note.getFilename(), note])
	
	def onLibraryRemoved(self,library:JD_EntLibrary):
		print(f'{DEBUG_PREFIX} onLibraryRemoved path:{library.path}')
		removal:List[Gtk.TreeIter] = []
		model:Gtk.TreeStore = self.treeView.get_model()
		for node in model:
			if node[1] == library:
				removal.append(node.iter)
		for node in removal:
			model.remove(node)

class JDSidePanelManager():
	side_panel:Xed.Panel = None
	panels:List[JDPanelTab] = []
	entityTracker:JD_EntTracker = None

	def __init__(self, panel:Xed.Panel, entityTracker:JD_EntTracker):
		print(f'{DEBUG_PREFIX} SidePanelManager __init__')
		self.side_panel = panel
		self.entityTracker = entityTracker

	def addTab(self, panelTab:JDPanelTab):
		print(f'{DEBUG_PREFIX} SidePanelManager addTab')
		self.side_panel.add_item(panelTab.GetWidget(), panelTab.display_name, panelTab.icon_name)
		self.entityTracker.subscribeLibraryAdded(panelTab.onLibraryAdded)
		self.entityTracker.subscribeLibraryRemoved(panelTab.onLibraryRemoved)
		# add libraries
		for library in self.entityTracker.GetLibraries():
			panelTab.onLibraryAdded(library) # TODO this will become for library in config.libraries addLibrary(lib).
		self.panels.append(panelTab)

	def getTab(self, tab_name:str):
		return self.panels[tab_name]

	def deactivate(self):
		print(f'{DEBUG_PREFIX} JDSidePanelManager.deactivate()')
		# TODO, should the TreeStores be explicitly set to None? 
		for panel in self.panels:
			print(f'{DEBUG_PREFIX} removing panel {panel.internal_name}')
			self.side_panel.remove_item(panel.GetWidget())
			panel.treeView.get_model().clear() # Is this necessary? Or will it be destroyed when we clear the widget.
			panel.widget_container = None # TODO move this code into panel.deactivate() method
		self.panels.clear()
		self.side_panel = None