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

Changes
-------

* Reduced our sync logic from 4 passes to 3 passes (integrating upload of
  "new" and "existing" messages into one function). This should result in a
  slight speedup.

Bug Fixes
---------


Pending for the next major release
==================================

* UIs get shorter and nicer names. (API changing)
* Implement IDLE feature. (delayed until next major release)


Stalled
=======

* Learn Sqlite support.
    Stalled: it would need to learn the ability to choose between the current
    format and SQL to help testing the long term.
