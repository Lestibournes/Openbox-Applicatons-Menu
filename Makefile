prefix = /

install:
	install obam $(DESTDIR)$(prefix)bin
	install -D -t $(DESTDIR)$(prefix)etc/xdg/obam/ footer config.json
	install -D menu.xml $(DESTDIR)$(prefix)etc/skel/.config/openbox
