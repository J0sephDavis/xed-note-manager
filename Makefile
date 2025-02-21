build:
	cp /media/d_drive/VisualStudioCode\ Projects/custom-xed-plugin/JD* ~/.local/share/xed/plugins/
run: build
	gdb --quiet /usr/bin/xed
