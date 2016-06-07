.. vim: spelllang=en ts=2 expandtab :

.. _coding style: https://github.com/OfflineIMAP/offlineimap/blob/next/docs/CodingGuidelines.rst

============================
TODO list by relevance order
============================

Should be the starting point to improve the `coding style`_.

Write your WIP directly in this file.

TODO list
---------

* Better names for variables, objects, etc.


* Improve comments.

  Most of the current comments assume a very good
  knowledge of the internals. That sucks because I guess nobody is
  anymore aware of ALL of them. Time when this was a one guy made
  project has long passed.


* Better policy on objects.

  - Turn ALL attributes private and use accessors. This is not
    "pythonic" but such pythonic thing turn the code into intricated
    code.

  - Turn ALL methods not intended to be used outside, private.


* Revamp the factorization.

  It's not unusual to find "factorized" code
  for bad reasons: because it made the code /look/ nicer, but the
  factorized function/methods is actually called from ONE place. While it
  might locally help, such practice globally defeat the purpose because
  we lose the view of what is true factorized code and what is not.


* Namespace the factorized code.

  If a method require a local function, DON'T USE yet another method. Use a
  local namespaced function.::

    class BLah(object):
        def _internal_method(self, arg):
            def local_factorized(local_arg):
                # local_factorized's code
            # _internal_method's code.

  Python allows local namespaced functions for good reasons.


* Better inheritance policy.

  Take the sample of the folder/LocalStatus(SQlite) and folder/Base stuffs. It's
  *nearly IMPOSSIBLE* to know and understand what parent method is used by what
  child, for what purpose, etc. So, instead of (re)defining methods in the wild,
  keep the well common NON-redefined stuff into the parent and define the
  required methods in the childs. We really don't want anything like::

    def method(self):
        raise NotImplemented

  While this is common practice in Python, think about that again: how a
  parent object should know all the expected methods/accessors of all the
  possible kind of childs?

  Inheritance is about factorizing, certainly **NOT** about **defining the
  interface** of the childs.


* Introduce as many as intermediate inherited objects as required.

  Keeping linear inheritance is good because Python sucks at playing
  with multiple parents and it keeps things simple. But a parent should
  have ALL its methods used in ALL the childs. If not, it's a good
  sign that a new intermediate object should be introduced in the
  inheritance line.

* Don't blindly inherit from library objects.

  We do want **well defined interfaces**. For example, we do too much things
  like imapobj.methodcall() while the imapobj is far inherited from imaplib2.

  We have NO clue about what we currently use from the library.
  Having a dump wrappper for each call should be made mandatory for
  objects inherited from a library. Using composed objects should be
  seriously considered in this case, instead of using inheritance.

* Use factories.

  Current objects do too much initialization stuff varying with the context it
  is used. Move things like that into factories and keep the objects definitions
  clean.


* Make it clear when we expect a composite object and what we expect
  exactly.

  Even the more obvious composed objects are badly defined. For example,
  the ``conf`` instances are spread across a lot of objects. Did you know
  that such composed objects are sometimes restricted to the section the
  object works on, and most of the time it's not restricted at all?
  How many time it requires to find and understand on what we are
  currently working?


* Seriously improve our debugging/hacking sessions (AGAIN).

  Until now, we have limited the improvements to allow better/full stack traces.
  While this was actually required, we now hit some limitations of the whole
  exception-based paradigm. For example, it's very HARD to follow an instance
  during its life time. I have a good overview of what we could do in this area,
  so don't matter much about that if you don't get the point or what could be
  done.

* Support Unicode.
