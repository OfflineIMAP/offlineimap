.. -*- coding: utf-8 -*-
.. vim: spelllang=en ts=2 expandtab:

.. _OfflineIMAP: https://github.com/OfflineIMAP/offlineimap
.. _Github: https://github.com/OfflineIMAP/offlineimap
.. _repository: git://github.com/OfflineIMAP/offlineimap.git
.. _maintainers: https://github.com/OfflineIMAP/offlineimap/blob/next/MAINTAINERS.rst
.. _mailing list: http://lists.alioth.debian.org/mailman/listinfo/offlineimap-project
.. _Developer's Certificate of Origin: https://github.com/OfflineIMAP/offlineimap/blob/next/docs/doc-src/dco.rst
.. _Community's website: https://offlineimap.github.io
.. _APIs in OfflineIMAP: http://offlineimap.github.io/documentation.html#available-apis
.. _documentation: https://offlineimap.github.io/documentation.html
.. _Coding Guidelines: http://offlineimap.github.io/doc/CodingGuidelines.html
.. _Know the status of your patches: http://localhost:4000/doc/GitAdvanced.html#know-the-status-of-your-patch-after-submission


=================
HOW TO CONTRIBUTE
=================

You'll find here the **basics** to contribute to OfflineIMAP_, addressed to
users as well as learning or experienced developers to quickly provide
contributions.

**For more detailed documentation, see the** `Community's website`_.

.. contents:: :depth: 3


For the imaptients
==================

- `Coding Guidelines`_
- `APIs in OfflineIMAP`_
- `Know the status of your patches`_ after submission
- All the `documentation`_


Submit issues
=============

Issues are welcome to both Github_ and the `mailing list`_, at your own
convenience.


Community
=========

All contributors to OfflineIMAP_ are benevolent volunteers. This makes hacking
to OfflineIMAP_ **fun and open**.

Thanks to Python, almost every developer can quickly become productive. Students
and novices are welcome. Third-parties patches are essential and proved to be a
wonderful source of changes for both fixes and new features.

OfflineIMAP_ is entirely written in Python, works on IMAP and source code is
tracked with Git.

*It is expected that most contributors don't have skills to all of these areas.*
That's why the best thing you could do for you, is to ask us about any
difficulty or question raising in your mind. We actually do our best to help new
comers. **We've all started like this.**

- The official repository_ is maintained by the core team maintainers_.

- The `mailing list`_ is where all the exciting things happen.


Getting started
===============

Occasional contributors
-----------------------

* Clone the official repository_.

Regular contributors
--------------------

* Create an account and login to Github.
* Fork the official repository_.
* Clone your own fork to your local workspace.
* Add a reference to your fork (once)::

  $ git remote add myfork https://github.com/<your_Github_account>/offlineimap.git

* Regularly fetch the changes applied by the maintainers::

  $ git fetch origin
  $ git checkout master
  $ git merge offlineimap/master
  $ git checkout next
  $ git merge offlineimap/next


Making changes (all contributors)
---------------------------------

1. Create your own topic branch off of ``next`` (recently updated) via::

   $ git checkout -b my_topic next

2. Check for unnecessary whitespaces with ``git diff --check`` before committing.
3. Commit your changes into logical/atomic commits.  **Sign-off your work** to
   confirm you agree with the `Developer's Certificate of Origin`_.
4. Write a good *commit message* about **WHY** this patch (take samples from
   the ``git log``).


Learn more
==========

There is already a lot of documentation. Here's where you might want to look
first:

- The directory ``offlineimap/docs`` has all kind of additional documentation
  (advanced Git, RFCs, APIs, coding guidelines, etc).

- The file ``offlineimap.conf`` allows to know all the supported features.

- The file ``TODO.rst`` express code changes we'd like and current *Work In
  Progress* (WIP).

