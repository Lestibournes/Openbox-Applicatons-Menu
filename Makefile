prefix = /

all:
	

install:
	install -D -t $(DESTDIR)$(prefix)usr/bin obam
	install -D -t $(DESTDIR)$(prefix)etc/xdg/obam footer config.json
	install -D -t $(DESTDIR)$(prefix)etc/skel/.config/openbox menu.xml

clean:
	