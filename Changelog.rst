=========
ChangeLog
=========

**NOTE FROM THE MAINTAINER:**
  Contributors should use the `WIP` section in order to add changes they are
  working on. I will use it to make the new changelog entry on releases. And
  because I'm lazy, it will also be used as a draft for the releases announces.
  Users should skip the `WIP` section: **it is a draft**.


`WIP (coming releases)`
=======================

.. Contributors should add entries here in the approppriate subsection, on top.

New Features
------------

* Makefile learn to build the package and make it the default.
* Introduce a Changelog.
* Migrate documentation to restructuredtext.

* UIs get shorter and nicer names.
    Pending until next major release.

* Learn Sqlite support.
    Stalled: it would need to learn the ability to choose between the current
    format and SQL to help testing the long term.


Changes
-------

* Imply single threading mode in debug mode exept for "-d thread".
* Code and import cleanups.
* Allow UI to have arbitrary names.
* Code refactoring around UI and UIBase.
* Improve version managment and make it easier.

Bug Fixes
---------

* Fixes in README.
* Only verify hostname if we actually use CA cert.
* Remove uneeded files.
* Fix makefile clean for files having whitespaces.
* Fix makefile to not remove unrelated files.
* Introduce a true single threading mode.
* Fix 'Ctrl+C' interruptions in threads.
* Fix ssl ca-cert in the sample configuration file.


.. Here comes history on what we did.

OfflineIMAP v6.3.2-rc1 (2010-12-19)
===================================

Notes
-----

We are beginning a tests cycle. If feature topics are sent, I may merge or
delay them until the next stable release.

New Features
------------

* Primitive implementation of SSL certificates check.

Changes
-------

* Use OptionParser instead of getopts.
* Code cleanups.

Bug Fixes
---------

* Fix reading password from UI.


OfflineIMAP v6.3.1 (2010-12-11)
===============================

Notes
-----

Yes, I know I've just annouced the v6.3.0 in the same week. As said, it
was not really a true release for the software. This last release
includes fixes and improvements it might be nice to update to.

Thanks to every body who helped to make this release with patches and
tips through the mailing list. This is clearly a release they own.

Changes
-------

* cProfile becomes the default profiler. Sebastian Spaeth did refactoring to
  prepare to the coming unit test suites.
* UI output formating enhanced.
* Some code cleanups.

Bug Fixes
---------

* Fix possible overflow while working with Exchange.
* Fix time sleep while exiting threads.


OfflineIMAP v6.3.0 (2010-12-09)
===============================

Notes
-----

This release is more "administrative" than anything else and mainly marks the
change of the maintainer. New workflow and policy for developers come in.  BTW,
I don't think I'll maintain debian/changelog. At least, not in the debian way.

Most users and maintainers may rather want to skip this release.

Bug Fixes
---------

* Fix terminal display on exit.
* netrc password authentication.
* User name querying from netrc.
