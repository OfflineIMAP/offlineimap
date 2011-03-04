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

* SSL: support subjectAltName.

Changes
-------

* Makefile use magic to find the version number.
* Rework the repository module

Bug Fixes
---------

* Allow SSL connections to send keep-alive messages.
* Fix regression (UIBase is no more).
* Make profiling mode really enforce single-threading
* Do not send localized date strings to the IMAP server as it will
  either ignore or refuse them.

Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)


Stalled
=======

* Learn Sqlite support.
    Stalled: it would need to learn the ability to choose between the current
    format and SQL to help testing the long term.
