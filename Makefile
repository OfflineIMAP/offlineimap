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

VERSION=4.0.16
TARGZ=offlineimap_$(VERSION).tar.gz
SHELL=/bin/bash

clean:
	-python setup.py clean --all
	-rm -f bin/offlineimapc
	-rm -f `find . -name "*.pyc"`
	-rm -f `find . -name "*.pygc"`
	-rm -f `find . -name "*.class"`
	-rm -f `find . -name ".cache*"`
	-rm -f manpage.links manpage.refs
	-find . -name auth -exec rm -vf {}/password {}/username \;
	-rm -f readme.html
	@$(MAKE) -C docs clean

man:
	@$(MAKE) -C docs man

doc: 
	@$(MAKE) -C docs
	rst2html.py README.rst readme.html
	rst2html.py SubmittingPatches.rst SubmittingPatches.html

targz: ../$(TARGZ)
../$(TARGZ):
	if ! pwd | grep -q "/offlineimap-$(VERSION)$$"; then 			\
	  echo "Containing directory must be called offlineimap-$(VERSION)"; 	\
	  exit 1; 								\
	fi; 									\
	pwd && cd .. && pwd && tar -zhcv --exclude '.git' -f $(TARGZ) offlineimap-$(VERSION)

rpm: targz
	cd .. && sudo rpmbuild -ta $(TARGZ)
