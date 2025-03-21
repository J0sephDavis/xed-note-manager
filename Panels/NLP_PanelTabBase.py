from NLP_Utils import DEBUG_PREFIX,new_menu_item, menu_separator,GetFileContents
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject
from gi.repository import Xed
from gi.repository import Gtk
from gi.repository import Gdk
from Entities.NLP_EntityLibrary import ELibrary
from Entities.NLP_EntityNote import ENote
from Entities.NLP_EntityBase import EBase
from Entities.NLP_EntityTemplate import ETemplate
from NLP_PrivateData import PrivateData
from Panels.NLP_TreeViewUtils import get_entites_from_model, ModelTraverseFlags
from typing import List,Tuple,Dict,Callable
from weakref import ref

def create_template_submenu(library:ELibrary,templates:List[ETemplate], handler:Callable):
	menu = Gtk.Menu()
	for template in templates:
		print(template.identifier)
		menu.append(new_menu_item(template.identifier,handler,template,library))
	menu.show_all()
	return menu

class PanelTabBase(Gtk.Box):

	def GetWidget(self): return self;

	def do_deactivate(self):
		self.window = None
		
		self.menu_items_base = []
		self.menu_items_note = []
		self.menu_items_library = []
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
	
	def __init__(self,
			  window:Xed.Window, treeModel:Gtk.TreeModel,			# gtk
			  internal_name:str, display_name:str, icon_name:str,	# some properties TODO (because its a GObject, shouldn't we install them?)
			  app_level_menu_items:List[Gtk.MenuItem], 				# menu_items is appended to the menu.
			  panel_level_menu_items:List[Gtk.MenuItem]): 			# only made within PanelTabBase (sub)classes)
		# ---- Properties ----
		self.window = window
		self.internal_name = internal_name 	# This should be unique, or at least unique to an implement class of PanelTabBase. Used in algorithms
		self.display_name = display_name	# For the user, it shows up in the UI menus
		self.icon_name = icon_name			# the icon name used by Gtk to resolve the displayed icon
		self.plugin_private_Data = PrivateData()
		# Dictionary of a weakreferenced object which we have a signal attached to, and the list of signal ids to disconnect.
		self.handles:Dict[ref[GObject.Object],List[int]] = {}
		# ----- TreeView -----
		super().__init__(spacing=6,orientation=Gtk.Orientation.VERTICAL)
		self.treeView = Gtk.TreeView(model=treeModel)

		treeView_handles = self.handles[ref(self.treeView)] = []
		treeView_handles.append(self.treeView.connect('button-release-event', self.handler_button_released))
		treeView_handles.append(self.treeView.connect('row-activated', self.handler_row_activated))

		self.pack_start(self.treeView,True,True,0)
		self.show_all()
		## ----- Popup Menu -----
		# TODO use separate lists so that they can be iterated over to do .show and .hide quickly
		self.menu_is_open:bool = False
		self.menu = Gtk.Menu()
		# template sub menu state
		self.menu_template_sub_menu = Gtk.MenuItem("Templates")
		self.last_selected_lib:ref[ELibrary] = None # used when checking if we should update the template_sub_menu
		self.menu_items_library = [
			self.menu_template_sub_menu,
			menu_separator()
		]
		# Note handlers
		self.menu_items_note = [new_menu_item("Copy YAML to Clipboard", self.handler_CopyFrontmatter),menu_separator()]
		# Base entity handlers (never hidden because everything is an entity? Except the day when there are 0 notes in a directory.... Open in explorer works without visible entities, but Delete definitely does not)
		self.menu_items_base = [
			new_menu_item("Delete entry", self.handler_DeleteSelectedFile),
			new_menu_item("Open in Explorer", self.handler_OpenNoteInFileExplorer),
			menu_separator(),
		]
		# ---
		app_level_menu_items.append(menu_separator())
		panel_debug_items = [
			new_menu_item("(DEBUG)Remove selected entry", self.handler_remove_selected),
			new_menu_item("(DEBUG) TEST", self.handler_unimplemented),
			menu_separator(),
		]
		panel_level_menu_items.extend(panel_debug_items)

		panel_entity_entries = []
		panel_entity_entries.extend(self.menu_items_base)
		panel_entity_entries.extend(self.menu_items_note)
		panel_entity_entries.extend(self.menu_items_library)
		
		all_menu_items:List = 		\
			panel_level_menu_items 	\
			+ panel_entity_entries	\
			+ app_level_menu_items
		
		for item in all_menu_items: self.menu.append(item)
		self.menu.show_all()
		self.menu.connect('show',self._menu_show_routine)
	# --- Gtk Menu
	def _menu_show_routine(self,menu):
		self._menu_show_library(menu)
		self._menu_show_note(menu)
		self._menu_remove_trailing_separators(menu)

	def _menu_remove_trailing_separators(self,menu):
		for item in reversed(menu.get_children()):
			if (item.props.visible):
				if isinstance(item,Gtk.SeparatorMenuItem):
					item.hide()
				else: return

	def _menu_show_library(self,menu):
		lib = self.GetCurrentlySelectedLibrary()
		if lib == self.last_selected_lib: return
		else: self.last_selected_lib = lib
		lib = lib()
		if lib is None:
			for item in self.menu_items_library:
				item.hide()
			return
		
		templates:List[ETemplate] = lib.GetTemplates()
		if templates is None or len(templates) == 0:
			self.menu_template_sub_menu.hide()
			# TODO currently there is only one element in the libraries section. but
			# in the future we will want to check if ANY are visible before hiding
			# this / if its the last separator in the list..
			
			# Maybe..., when adding menu items to the menu use a tuple of (MenuItem, func()) where func(menuitem) is run to determine if its shown or not... if all functions return False hide the separator as if it were never there..
			self.menu_items_library[-1].hide() #separator
			return
		self.menu_template_sub_menu.set_submenu(create_template_submenu(lib,templates,self.handler_create_from_template))
		self.menu_template_sub_menu.show_all()
		self.menu_items_library[-1].show() #separator

	def _menu_show_note(self,menu):
		iter,base_ref = self.GetCurrentlySelected()
		if type(base_ref()) is ENote:
			for item in self.menu_items_note: item.show()
		else:
			for item in self.menu_items_note: item.hide()

	# <<< METHODS >>>
	# # returns the library associated with the currently selected entry.
	def GetCurrentlySelectedLibrary(self)->ref[ELibrary]|None:
		selection = self.treeView.get_selection()
		if selection.get_mode() == Gtk.SelectionMode.MULTIPLE:
			return None
		(model,iter)=selection.get_selected()
		if iter is None: return None
		entry = model[iter][1]
		if issubclass(type(entry()),ELibrary):
			return entry
		parent_iter = model.iter_parent(iter)
		if parent_iter is None:
			print('batman')
			return None
		entry = model[parent_iter][1]
		if issubclass(type(entry()), ELibrary):
			return entry
	# returns the TreeIter to the currently highlight row + a weakref to entity
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
		raise NotImplemented("paneltab base TryFocusNote not implemented")

	# <<< HANDLERS >>>
	def handler_button_released(self, view:Gtk.TreeView, event):
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
	
	def handler_unimplemented(self, arg):
		print(f'{DEBUG_PREFIX} unimplemented menu item {arg}')

	def handler_CopyFrontmatter(self,widget):
		ent = self.GetCurrentlySelected()[1]()
		if (type(ent) != ENote): return
		frontmatter:str = ent.get_yaml_as_str()
		clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
		clipboard.set_text(frontmatter, -1)

	def handler_DeleteSelectedFile(self,widget):
		ent = self.GetCurrentlySelected()[1]()
		ent_type = type(ent)
		if issubclass(ent_type,EBase) == False: return # override the menu maker / somehow set a sensitivity for what will be shown and not shown (given the current selection)
		if ent_type is ENote:
			self.OnNoteRemoved(self,ent)
		elif ent_type is ELibrary:
			self.OnLibraryRemoved(self,ent)
		ent.delete()

	def handler_OpenNoteInFileExplorer(self, widget):
		ent = self.GetCurrentlySelected()[1]
		if ent is not None:
			ent = ent()
			if (issubclass(type(ent),EBase)):
				ent.open_in_explorer()
				return
		lib:ref[ELibrary]=self.GetCurrentlySelectedLibrary()
		if lib is None: return
		lib().open_in_explorer()
	
	# DEBUG only. Remove in PROD
	# removes the selected entity from the model (removes ALL of them)
	def handler_remove_selected(self, widget):
		entry_ent = self.GetCurrentlySelected()[1]()
		if (entry_ent is None): return
		if (type(entry_ent) is ELibrary):
			self.OnLibraryRemoved(self.handler_remove_selected, entry_ent)
		elif (type(entry_ent) is ENote):
			self.OnNoteRemoved(self.handler_remove_selected, entry_ent)
		else:
			print(f'{DEBUG_PREFIX} ERR remove_selected unhandled entity, {type(entry_ent)}')
			return

	def handler_create_from_template(self,widget,template:ETemplate,library:ELibrary):
		note_was_created, note = library.CreateFromTemplate(template)
		self.TryFocusNote(note)
		note.open_in_new_tab(self.window)

	# <<< EVENTS >>>
	def OnNoteAdded(self, library:ELibrary, note:ENote): pass
	def OnNoteRemoved(self, library:ELibrary, note:ENote): pass

	def OnLibraryAdded(self, library:ELibrary, note:ENote): pass
	def OnLibraryRemoved(self, library:ELibrary, note:ENote): pass