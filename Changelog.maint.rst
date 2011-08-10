=========
ChangeLog
=========

:website: http://offlineimap.org

This is the Changelog of the maintenance branch.

**NOTE FROM THE MAINTAINER:**
  Contributors should use the `WIP` section in Changelog.draft.rst in order to
  add changes they are working on. I will use it to make the new changelog entry
  on releases. And because I'm lazy, it will also be used as a draft for the
  releases announces.


OfflineIMAP v6.3.2.3 (2011-08-10)
=================================

Changes
-------

* Output more detailed error on corrupt LocalStatus.
* More detailed error output on corrupt UID mapping files.

Bug Fixes
---------

* Fix typo to force singlethreading in debug mode.


OfflineIMAP v6.3.2.2 (2011-04-24)
=================================

Changes
-------

* Improve traceback on some crashes.


OfflineIMAP v6.3.2.1 (2011-03-23)
=================================

Bug Fixes
---------

* Sanity checks for SSL cacertfile configuration.
* Fix regression (UIBase is no more).
* Make profiling mode really enforce single-threading.
