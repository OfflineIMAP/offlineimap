# Copyright (C) 2002 - 2006 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

VERSION=$(shell ./offlineimap.py --version)
ABBREV=$(shell git log --format='%h' HEAD~1..)
TARGZ=offlineimap-$(VERSION)-$(ABBREV)
SHELL=/bin/bash
RST2HTML=`type rst2html >/dev/null 2>&1 && echo rst2html || echo rst2html.py`

all: build

build:
	python setup.py build
	@echo
	@echo "Build process finished, run 'python setup.py install' to install" \
		"or 'python setup.py --help' for more information".

clean:
	-python setup.py clean --all
	-rm -f bin/offlineimapc 2>/dev/null
	-find . -name '*.pyc' -exec rm -f {} \;
	-find . -name '*.pygc' -exec rm -f {} \;
	-find . -name '*.class' -exec rm -f {} \;
	-find . -name '.cache*' -exec rm -f {} \;
	-rm -f manpage.links manpage.refs 2>/dev/null
	-find . -name auth -exec rm -vf {}/password {}/username \;
	@$(MAKE) -C clean

.PHONY: docs
docs:
	@$(MAKE) -C docs

websitedoc:
	@$(MAKE) -C websitedoc

targz: ../$(TARGZ)
../$(TARGZ):
	cd .. && tar -zhcv --transform s,^offlineimap,$(TARGZ), -f $(TARGZ).tar.gz --exclude '*.pyc' offlineimap/{bin,Changelog.md,contrib,CONTRIBUTING.rst,COPYING,docs,MAINTAINERS.rst,MANIFEST.in,offlineimap,offlineimap.conf,offlineimap.conf.minimal,offlineimap.py,README.md,scripts,setup.py,test,TODO.rst}

rpm: targz
	cd .. && sudo rpmbuild -ta $(TARGZ)
