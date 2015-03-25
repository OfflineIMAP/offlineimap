# This program is free software under the terms of the GNU General Public
# License. See the COPYING file which must come with this package.

SOURCES = $(wildcard *.rst)
HTML_TARGETS = $(patsubst %.rst,%.html,$(SOURCES))

RM = rm
RST2HTML=`type rst2html >/dev/null 2>&1 && echo rst2html || echo rst2html.py`
RST2MAN=`type rst2man >/dev/null 2>&1 && echo rst2man || echo rst2man.py`
SPHINXBUILD = sphinx-build

docs: man api

html: $(HTML_TARGETS)

$(HTML_TARGETS): %.html : %.rst
	$(RST2HTML) $? $@

man: offlineimap.1 offlineimapui.7

offlineimap.1: offlineimap.txt
	a2x -v -f manpage $?

offlineimapui.7: offlineimapui.txt
	a2x -v -f manpage $?

api:
	$(SPHINXBUILD) -b html -d html/doctrees doc-src html

websitedoc:
	./website-doc.sh releases
	./website-doc.sh api
	./website-doc.sh contrib

clean:
	$(RM) -f $(HTML_TARGETS)
	$(RM) -f offlineimap.1
	$(RM) -f offlineimap.7
	$(RM) -rf html/*
	-find ./docs -name '*.html' -exec rm -f {} \;

.PHONY: clean doc
