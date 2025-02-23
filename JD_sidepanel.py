import gi
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import GLib

from JD__entities import *
from JD__utils import DEBUG_PREFIX
from typing import List
# Considerations
# - how to preserve the JD_EntNode relationship so they can be opened?
# - do we have to clean any of this up? Or is it fine to just let it die with the process?
# Functional TODO
# - Get the TreeIter under the cursor
# - Track the last two TreeIter selected
# - if Iter A & B are the same, open the file / act on it
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
	def __init__(self, window:Xed.Window):
		super().__init__()
		print(f'{DEBUG_PREFIX} PanelTab __init__')
		# self.library_nodes:List[Tuple[JD_EntLibrary,Gtk.TreeIter]] = [] # str:library name
		self.handlers:List[int] = []
		# COLUMNS: filename,
		self.treeStore:Gtk.TreeStore = Gtk.TreeStore(str, GObject.TYPE_PYOBJECT)
		self.treeView:Gtk.TreeView = Gtk.TreeView(model=self.treeStore)
		
		self.treeView.insert_column(
			Gtk.TreeViewColumn(title='name', cell_renderer=Gtk.CellRendererText(),text=0),
			position=-1
		)
		# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeView.html#signals
		self.handlers.append(self.treeView.connect("row-activated", self.handler_row_activated, window))


	def handler_row_activated(self, treeview, path, col, window):
		count_selection = treeview.get_selection().count_selected_rows()
		if count_selection > 1: return
		print(f'{DEBUG_PREFIX} !!!row-ativated:\n\tpath{path}\n\tselection-size:{count_selection}')
		model = treeview.get_model()
		iter:Gtk.TreeIter = model.get_iter(path)
		model[iter][1].open_in_new_tab(window)
		# iter:Gtk.TreeIter = self.treeStore.get_iter(path)

	def getWidget(self): return self.treeView
	def getStore(self): return self.treeStore
	# TODO name+icon should be instance vars
	def getName(self): return "namegoeshere"
	def getIcon(self): return "folder" # this is from the users icon theme. lookup some more

	def addLibrary(self, library:JD_EntLibrary):
		print(f'{DEBUG_PREFIX} PanelTab addLibrary')
		node:Gtk.TreeIter = self.treeStore.append(None, [library.getFilename(), library])
		# self.library_nodes.append((library,node))

		for note in library.notes:
			self.treeStore.append(node, [note.getFilename(), note])

class JDSidePanelManager():
	def __init__(self, panel:Xed.Panel):
		print(f'{DEBUG_PREFIX} SidePanelManager __init__')
		self.side_panel = panel
	
	def addTab(self, panelTab:JDPanelTab):
		print(f'{DEBUG_PREFIX} SidePanelManager addTab')
		self.side_panel.add_item(panelTab.getWidget(), panelTab.getName(), panelTab.getIcon())

