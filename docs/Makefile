# This program is free software under the terms of the GNU General Public
# License. See the COPYING file which must come with this package.

SOURCES = $(wildcard *.rst)
HTML_TARGETS = $(patsubst %.rst,%.html,$(SOURCES))

RM = rm
RST2HTML=`type rst2html >/dev/null 2>&1 && echo rst2html || echo rst2html.py`
RST2MAN=`type rst2man >/dev/null 2>&1 && echo rst2man || echo rst2man.py`
SPHINXBUILD = sphinx-build

all: man doc

html: $(HTML_TARGETS)

$(HTML_TARGETS): %.html : %.rst
	$(RST2HTML) $? $@

man: offlineimap.1

offlineimap.1: MANUAL.rst
	$(RST2MAN) MANUAL.rst offlineimap.1
	cp -f offlineimap.1 ..

doc:
	$(SPHINXBUILD) -b html -d html/doctrees doc-src html

clean:
	$(RM) -f $(HTML_TARGETS)
	$(RM) -f offlineimap.1 ../offlineimap.1
	$(RM) -rf html/*

.PHONY: clean doc
