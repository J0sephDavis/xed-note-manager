from NLP_Utils import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import GObject
from gi.repository import Xed
from gi.repository import Gtk
from Entities.NLP_EntityLibrary import ELibrary
from Entities.NLP_EntityNote import ENote
from Entities.NLP_EntityBase import EBase
from Entities.NLP_EntityManager import EntityManager
from NLP_PrivateData import PrivateData
from Panels.NLP_TreeViewUtils import get_entites_from_model, ModelTraverseFlags, del_entries_from_model
from typing import List,Tuple,Dict
from weakref import ref
class PanelTabBase(Gtk.Box):

	def GetWidget(self): return self;

	def do_deactivate(self):
		self.menu.foreach(lambda widget: widget.destroy())
		for obj in self.handles:
			ent = obj()
			# assumed to be our most common case
			if (type(ent) is ELibrary): self.OnLibraryRemoved(self,ent)
			# uncommon case
			elif type(ent) is None: continue
			else: # default case
				for handle in self.handles[obj]:
					ent.disconnect(handle)
		self.handles.clear()
		self.plugin_private_Data = None
		self.treeView.get_model().clear()
	
	def __init__(self, window:Xed.Window, treeModel:Gtk.TreeModel, internal_name:str, display_name:str, icon_name:str): #, menu_items:List[Gtk.MenuItem]):
		self.window = window
		self.internal_name = internal_name 	# This should be unique, or at least unique to an implement class of PanelTabBase. Used in algorithms
		self.display_name = display_name	# For the user, it shows up in the UI menus
		self.icon_name = icon_name			# the icon name used by Gtk to resolve the displayed icon
		self.plugin_private_Data = PrivateData()
		# Dictionary of a weakreferenced object which we have a signal attached to, and the list of signal ids to disconnect.
		self.handles:Dict[ref[GObject.Object],List[int]] = {}
		# Setup the main widget
		super().__init__(spacing=6,orientation=Gtk.Orientation.VERTICAL)
		self.treeView = Gtk.TreeView(model=treeModel)

		tree_handles = self.handles[ref(self.treeView)] = []
		tree_handles.append(self.treeView.connect('button-release-event', self.handler_button_released))
		tree_handles.append(self.treeView.connect('row-activated', self.handler_row_activated))

		self.pack_start(self.treeView,True,True,0)
		self.show_all() # TODO make base class responsibility? Maybe its best to use builder methods to make our panels...
		# Popup Menu
		# TODO move responsbility to base class? Or builder method? Or leave as-is
		# TODO Gio.MenuModel
		self.menu = Gtk.Menu()
		# for item in menu_items:
		# 	self.menu.append(item)
		# self.menu.show_all()
		
	def GetCurrentlySelected(self)->Tuple[Gtk.TreeIter,ref[EBase]]:
		selection = self.treeView.get_selection()
		if (selection.get_mode() == Gtk.SelectionMode.MULTIPLE):
			print(f'{DEBUG_PREFIX} multiple selection TODO..')
			return None
		(model,iter)=selection.get_selected()
		if (iter is not None):
			entry =  model[iter][1]
			if issubclass(type(entry()), EBase):
				retval =  (model.iter_parent(iter), entry) # parent, selected
				return retval
		return None, None

	def _get_note(self, note:ENote) -> Gtk.TreePath|None: # TODO private method. TreeStore specific
		print(f'{DEBUG_PREFIX} GetNote: {note}')
		found:List[Gtk.TreePath] = get_entites_from_model(self.treeView.get_model(), ref(note), ModelTraverseFlags.EARLY_RETURN | ModelTraverseFlags.RET_PATH)
		if len(found) < 1:
			return None
		return found[0]
	
	def TryFocusNote(self,note:ENote)->bool:
		print(f'{DEBUG_PREFIX} EXCEPTION PanelTabBase.TryFocusNote NOT IMPLEMENTED')
		return False

	# <<< HANDLERS / CALLBACKS >>>
	def handler_button_released(self, view, event):
		if (event.button != 3): return False # Propagate signal
		# If a right click is received, while the menu is closed,
		# the element below the cursor will be selected (GOOD)
		# If a right click is received, while the menu is open,
		# the selection will not be changed (BAD)
		
		# because MenuShell('deactivate') is called when you right click, you can't readily know if the popup WAS open when the user right clicked.
		# there is definitely a way, I just do not know it atm.
		path_tuple = self.treeView.get_path_at_pos(event.x,event.y)
		if (path_tuple is not None and path_tuple[0] is not None):
			self.treeView.set_cursor(path_tuple[0],None,None)
		
		self.menu.popup_at_pointer(event)
		self.menu_is_open = True
		return True # Do not propagate signal

	def handler_row_activated(self, caller:Gtk.TreeView, path, col): # make into a module function instead of class method?
		model = caller.get_model() # Either a TreeStore or a ListStore should be fine here.
		iter:Gtk.TreeIter = model.get_iter(path)
		base = model[iter][1]()
		if (type(base) is ENote):
			base.open_in_new_tab(self.window)
		elif (type(base) is ELibrary):
			base.open_in_explorer()