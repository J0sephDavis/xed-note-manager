build:
	mkdir -p ~/.local/share/xed/plugins/NoteLibraryPlugin
	cp -r /media/d_drive/VisualStudioCode\ Projects/custom-xed-plugin/* ~/.local/share/xed/plugins/NoteLibraryPlugin
run: build
	gdb --quiet /usr/bin/xed
