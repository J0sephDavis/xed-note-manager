build:
	cp -r /media/d_drive/VisualStudioCode\ Projects/custom-xed-plugin/* ~/.local/share/xed/plugins/
run: build
	gdb --quiet /usr/bin/xed
