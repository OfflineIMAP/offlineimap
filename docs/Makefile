# This program is free software under the terms of the GNU General Public
# License. See the COPYING file which must come with this package.

SOURCES = $(wildcard *.rst)
HTML_TARGETS = $(patsubst %.rst,%.html,$(SOURCES))

RM = rm

all: html

html: $(HTML_TARGETS)

$(HTML_TARGETS): %.html : %.rst
	rst2html.py $? $@

man: offlineimap.1

offlineimap.1: MANUAL.rst
	rst2man.py MANUAL.rst offlineimap.1
	cp -f offlineimap.1 ..

clean:
	$(RM) -f $(HTML_TARGETS)
	$(RM) -f offlineimap.1 ../offlineimap.1
