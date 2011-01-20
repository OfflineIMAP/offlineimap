=========
ChangeLog
=========

Users should ignore this content: **it is draft**.

Contributors should add entries here in the following section, on top of the
others.

`WIP (coming releases)`
=======================

New Features
------------

* Makefile learn to build the package and make it the default.
* Introduce a Changelog.
* Migrate documentation to restructuredtext.

Changes
-------

* Improve CustomConfig documentation.
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

Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)


Stalled
=======

* Learn Sqlite support.
    Stalled: it would need to learn the ability to choose between the current
    format and SQL to help testing the long term.
