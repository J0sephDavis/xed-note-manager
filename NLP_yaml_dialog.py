from NoteLibraryPlugin import DEBUG_PREFIX
import gi
gi.require_version('Xed', '1.0')
gi.require_version('PeasGtk', '1.0')
from gi.repository import Gtk
from gi.repository import Gio

# https://python-gtk-3-tutorial.readthedocs.io/en/latest/dialogs.html
class JDPlugin_Dialog_1(Gtk.Window): 
	def __init__(self, current_search, provided_callback):
		self.callback = provided_callback

		super().__init__(title="JDPlugin Dialog 1")
		self.set_default_size(150,100)

		self.box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		self.add(self.box)

		self.entry = Gtk.Entry()
		self.entry.set_text(current_search)
		self.box.pack_start(self.entry, True, True, 10)
		
		self.button_okay = Gtk.Button(label="Close")
		self.button_okay.connect("clicked", self.on_clicked_okay)
		self.box.pack_start(self.button_okay,expand=True,fill=True,padding=0);

		self.show_all()
	def on_clicked_okay(self, widget):
		print(f'{DEBUG_PREFIX} {self.entry.get_text()}')
		print(f'{DEBUG_PREFIX} closing dialog. ')
		self.callback(self.entry.get_text())
		self.destroy()

class JDPlugin_FileInformation_Window(Gtk.Window):
	def __init__(self, fInfo:Gio.FileInfo):
		super().__init__(title=f'File Information: {fInfo.get_name()}')
		self.set_default_size(256,128)
		self.fileInfo = fInfo;
		# table H
		self.table = Gtk.Box(spacing=6, orientation=Gtk.Orientation.HORIZONTAL)
		#colV 1 colV 2
		self.col_labels = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
		self.col_values = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)

		self._AddName()
		self._AddFileType()
		self._AddSize()
		self._AddCanRead()
		self._AddModifiedTime()
		self._AddContentType()
		
		self.table.pack_start(self.col_labels,True,True,0)
		self.table.pack_start(self.col_values,True,True,0)
		self.add(self.table)
		self.show_all()
		
	def _AddLabel(self, text:str):
		self.col_labels.pack_start(Gtk.Label(label=text),True,True,0)
	def _AddValue(self, text:str):
		self.col_values.pack_start(Gtk.Label(label=text),True,True,0)
	
	def _AddName(self):
		name = self.fileInfo.get_name()
		self._AddLabel("Name")
		self._AddValue(name)
	def _AddSize(self):
		size = self.fileInfo.get_size().__str__()
		self._AddLabel("Size")
		self._AddValue(size.__str__())
	def _AddCanRead(self):
		canRead = self.fileInfo.get_attribute_boolean(r'access::can_read').__str__()
		self._AddLabel("Can Read?")
		self._AddValue(canRead)
	def _AddModifiedTime(self):
		time = self.fileInfo.get_modification_date_time().format_iso8601()
		self._AddLabel("Modified")
		self._AddValue(time)
	def _AddContentType(self):
		contentType = self.fileInfo.get_content_type()
		self._AddLabel("Content Type")
		self._AddValue(contentType)
	def _AddFileType(self):
		fType = self.fileInfo.get_file_type().value_name
		self._AddLabel("File Type")
		self._AddValue(fType)


# class JDPlugin_Dialog_WithText(Gtk.Window):
# 	def __init__(self, filename:str, yaml_data):
# 		super().__init__(title=filename)
# 		self.box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
# 		self.add(self.box)

# 		self.text_box = Gtk.TextView()
# 		self.text_buffer = self.text_box.get_buffer()
# 		self.text_buffer.set_text(yaml_data.__str__())
# 		self.box.pack_start(self.text_box, True, True, 0)

# 		self.button_close = Gtk.Button(label="Close")
# 		self.button_close.connect("clicked", self.on_clicked_closed)
# 		self.box.pack_start(self.button_close,True,True,0)

# 		self.show_all()
	
# 	def on_clicked_closed(self, widget):
# 		print(f'{DEBUG_PREFIX} close')
# 		self.destroy()


# GtkDialog properties https://lazka.github.io/pgi-docs/Gtk-3.0/classes/Dialog.html
# GtkWindow properties https://lazka.github.io/pgi-docs/Gtk-3.0/classes/Window.html#gtk-window-props
# GtkContainer properties https://lazka.github.io/pgi-docs/Gtk-3.0/classes/Container.html#gtk-container-props
# GtkWidget properties https://lazka.github.io/pgi-docs/Gtk-3.0/classes/Widget.html#gtk-widget-props

# dialog_ui_string = """
# <?xml version="1.0"?>
# <interface>
# 	<object class="GtkDialog" id="JD_Dialog">
# 		<property name="title">Configure Notes Plugin</property>
# 		<property name="type">GTK_WINDOW_TOPLEVEL</property>
# 		<property name="window_poisiton">GTK_WIN_POST_NONE</property>
# 		<property name="modal">False</property>
# 		<property name="resizable">True</property>
# 		<property name="destroy_with_parent">True</property>
#     	<property name="type_hint">GDK_WINDOW_TYPE_HINT_DIALOG</property>
#     	<property name="focus_on_map">True</property>
# 		<property name="decorated">True</property>
# 		<child internal-child="vbox">
# 			<object class="GtkBox" id="JD_Dialog_Vbox_1">
# 				<property name="orientation">Vertical</property>
# 				<property name="expand">True</property>
# 				<child>
# 					<object class="GtkLabel" id="first_label">
						
# 					</object>
# 				</child>
# 			</object>
# 		</child>
# 	</object>
# </interface>
# """