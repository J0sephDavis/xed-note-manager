from NoteLibraryPlugin import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Xed
from gi.repository import Gtk
from gi.repository import Gio
from gi.repository import GLib
from NLP_Utils import OpenPathInFileExplorer
from Entities.NLP_EntityBase import EBase
# BUG ---------------------------
# open a note in a new tab
# move the note to a new window
# open the same note in a new tab (in the new window)
# It will open a duplicate tab instead of referencing the current one
# -------------------------------

class ENote(EBase):
	def __init__(self, file:Gio.File):
		super().__init__(file=file,icon='text-x-generic')

	def open_in_explorer(self): OpenPathInFileExplorer(self.get_base_dir())

	def open_in_new_tab(self, window:Xed.Window)->Xed.Tab:
		tab:Xed.Tab = window.get_tab_from_location(self.file)
		if tab is None:
			tab = window.create_tab_from_location(self.file,None,0,0,True)
		window.set_active_tab(tab)
		return tab
	
	def create(self, contents:bytes) -> bool:
		if contents is None: return False
		if self.exists(): raise False
		ostream:Gio.FileOutputStream = self.file.create(Gio.FileCreateFlags.NONE,None)
		if ostream is None: return False
		try:
			is_success,bytes_written = ostream.write_all(contents,None)
			if is_success:
				print(f'{DEBUG_PREFIX} ENote.create, wrote {bytes_written} bytes to file {self.get_path()}')
			else:
				print(f'{DEBUG_PREFIX} ENote.create, is_success==FALSE, wrote {bytes_written} bytes to file {self.get_path()}')
		except GLib.Error as e:
			print(f'-----\n{DEBUG_PREFIX} EXCEPTION in ENote.Create:\ndomain:{e.domain}\tcode{e.code}\targs{e.args}\nmessage:{e.message}\n-----')
		finally:
			ostream.close()
		return is_success