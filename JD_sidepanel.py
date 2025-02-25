import gi
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Xed
from gi.repository import GLib

from JD__entities import *
from JD__utils import DEBUG_PREFIX
from typing import List

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
		# COLUMNS: filename,
		self.treeStore:Gtk.TreeStore = Gtk.TreeStore(str, GObject.TYPE_PYOBJECT)
		self.treeView:Gtk.TreeView = Gtk.TreeView(model=self.treeStore)
		
		self.treeView.insert_column(
			Gtk.TreeViewColumn(title='name', cell_renderer=Gtk.CellRendererText(),text=0),
			position=-1
		)
		# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeView.html#signals
		self.treeView.connect("row-activated", self.handler_row_activated, window)

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
			self.treeStore.remove(selected_iter)
		else:
			print(f'{DEBUG_PREFIX} selected entry is not a library {entry[0]}, {type(entry[1])}')
			return

	def getWidget(self):
		widget_box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		remove_item_button = Gtk.Button(label="Remove Selected")
		remove_item_button.connect("clicked", self.handler_remove_selected)
		widget_box.pack_start(remove_item_button,False,True,5)
		widget_box.pack_start(self.treeView,True,True,0)

		widget_box.show_all() # Some widgets are hidden by default. Supposedly ALL are, but the TreeView is evidently made visible when it alone is returned. but using a container it is hidden...
		return widget_box # self.treeView

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
	
	def removeLibrary(self,library_path:str):
		print(f'{DEBUG_PREFIX} PanelTab removeLibrary(library_path={library_path})')
		if library_path is None: return
		removal:List[Gtk.TreeIter] = []
		for node in self.treeStore:
			if node[1].path == library_path:
				print(f'{DEBUG_PREFIX} library iter found,')
				removal.append(node.iter)
		for node in removal:
			self.treeStore.remove(node)

class JDSidePanelManager(): # This was not really thought out. This shoudl be turned into a function in the utils.py file. Doesn't do much
	def __init__(self, panel:Xed.Panel):
		print(f'{DEBUG_PREFIX} SidePanelManager __init__')
		self.side_panel = panel
	
	def addTab(self, panelTab:JDPanelTab):
		print(f'{DEBUG_PREFIX} SidePanelManager addTab')
		self.side_panel.add_item(panelTab.getWidget(), panelTab.getName(), panelTab.getIcon())
	
	def deactivate(self):
		# remove added widgets from sidepanel
		pass
		