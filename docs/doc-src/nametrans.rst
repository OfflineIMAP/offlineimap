.. _folder_filtering_and_name_translation:

Folder filtering and Name translation
=====================================

OfflineImap provides advanced and potentially complex possibilities for
filtering and translating folder names. If you don't need any of this, you can
safely skip this section.

.. warning::
   Starting with v6.4.0, OfflineImap supports the creation of folders on the remote repostory. This change means that people that only had a nametrans option on the remote repository (everyone) will need to have a nametrans setting on the local repository too that will reverse the name transformation. See section `Reverse nametrans`_ for details.

folderfilter
------------

If you do not want to synchronize all your folders, you can specify a
`folderfilter`_ function that determines which folders to include in a sync and
which to exclude. Typically, you would set a folderfilter option on the remote
repository only, and it would be a lambda or any other python function.

The only parameter to that function is the folder name. If the filter
function returns True, the folder will be synced, if it returns False,
it. will be skipped. The folderfilter operates on the *UNTRANSLATED*
name (before any `nametrans`_ fudging takes place). Consider the
examples below to get an idea of what they do.

Example 1: synchronizing only INBOX and Sent::

   folderfilter = lambda folder: folder in ['INBOX', 'Sent']

Example 2: synchronizing everything except Trash::

   folderfilter = lambda folder: folder not in ['Trash']

Example 3: Using a regular expression to exclude Trash and all folders
containing the characters "Del"::

    folderfilter = lambda folder: not re.search('(^Trash$|Del)', folder)

.. note::
   If folderfilter is not specified, ALL remote folders will be
   synchronized.

You can span multiple lines by indenting the others.  (Use backslashes
at the end when required by Python syntax)  For instance::

 folderfilter = lambda foldername: foldername in
        ['INBOX', 'Sent Mail', 'Deleted Items',
         'Received']

Usually it suffices to put a `folderfilter`_ setting in the remote repository
section. You might want to put a folderfilter option on the local repository if
you want to prevent some folders on the local repository to be created on the
remote one. (Even in this case, folder filters on the remote repository will
prevent that)

folderincludes
--------------

You can specify `folderincludes`_ to manually include additional folders to be
synced, even if they had been filtered out by a folderfilter setting.
`folderincludes`_ should return a Python list.

This can be used to 1) add a folder that was excluded by your
folderfilter rule, 2) to include a folder that your server does not specify
with its LIST option, or 3) to include a folder that is outside your basic
`reference`. The `reference` value will not be prefixed to this folder
name, even if you have specified one.  For example::

   folderincludes = ['debian.user', 'debian.personal']

This will add the "debian.user" and "debian.personal" folders even if you
have filtered out everything starting with "debian" in your folderfilter
settings.


createfolders
-------------

By default OfflineImap propagates new folders in both
directions. Sometimes this is not what you want. E.g. you might want
new folders on your IMAP server to propagate to your local MailDir,
but not the other way around. The 'readonly' setting on a repository
will not help here, as it prevents any change from occuring on that
repository. This is what the `createfolders` setting is for. By
default it is `True`, meaning that new folders can be created on this
repository. To prevent folders from ever being created on a
repository, set this to `False`. If you set this to False on the
REMOTE repository, you will not have to create the `Reverse
nametrans`_ rules on the LOCAL repository.


nametrans
----------

Sometimes, folders need to have different names on the remote and the local
repositories. To achieve this you can specify a folder name translator.  This
must be a eval-able Python expression that takes a foldername arg and returns
the new value.  We suggest a lambda function, but it could be any python
function really. If you use nametrans rules, you will need to set them both on
the remote and the local repository, see `Reverse nametrans`_ just below for
details. The following examples are thought to be put in the remote repository
section.

The below will remove "INBOX." from the leading edge of folders (great
for Courier IMAP users)::

   nametrans = lambda folder: re.sub('^INBOX\.', '', folder)

Using Courier remotely and want to duplicate its mailbox naming
locally?  Try this::

   nametrans = lambda folder: re.sub('^INBOX\.*', '.', folder)

.. warning::
    You MUST construct nametrans rules such that it NEVER returns the
    same value for two folders, UNLESS the second values are filtered
    out by folderfilter below. That is, two filters on one side may
    never point to the same folder on the other side. Failure to follow
    this rule will result in undefined behavior. See also *Sharing a
    maildir with multiple IMAP servers* in the :ref:`pitfalls` section.


Reverse nametrans
+++++++++++++++++

Since 6.4.0, OfflineImap supports the creation of folders on the remote
repository and that complicates things. Previously, only one nametrans setting
on the remote repository was needed and that transformed a remote to a local
name. However, nametrans transformations are one-way, and OfflineImap has no way
using those rules on the remote repository to back local names to remote names.

Take a remote nametrans rule `lambda f: re.sub('^INBOX/','',f)` which cuts off
any existing INBOX prefix. Now, if we parse a list of local folders, finding
e.g. a folder "Sent", is it supposed to map to "INBOX/Sent" or to "Sent"? We
have no way of knowing. This is why **every nametrans setting on a remote
repository requires an equivalent nametrans rule on the local repository that
reverses the transformation**.

Take the above examples. If your remote nametrans setting was::

   nametrans = lambda folder: re.sub('^INBOX\.', '', folder)

then you will want to have this in your local repository, prepending "INBOX" to
any local folder name::

   nametrans = lambda folder: 'INBOX.' + folder

Failure to set the local nametrans rule will lead to weird-looking error
messages of -for instance- this type::

  ERROR: Creating folder moo.foo on repository remote
  Folder 'moo.foo'[remote] could not be created. Server responded: ('NO', ['Unknown namespace.'])

(This indicates that you attempted to create a folder "Sent" when all remote
folders needed to be under the prefix of "INBOX.").

OfflineImap will make some sanity checks if it needs to create a new
folder on the remote side and a back-and-forth nametrans-lation does not
yield the original foldername (as that could potentially lead to
infinite folder creation cycles).

You can probably already see now that creating nametrans rules can be a pretty
daunting and complex endeavour. Check out the Use cases in the manual. If you
have some interesting use cases that we can present as examples here, please let
us know.

Debugging folderfilter and nametrans
------------------------------------

Given the complexity of the functions and regexes involved, it is easy to
misconfigure things. One way to test your configuration without danger to
corrupt anything or to create unwanted folders is to invoke offlineimap with the
`--info` option.

It will output a list of folders and their transformations on the screen (save
them to a file with -l info.log), and will help you to tweak your rules as well
as to understand your configuration. It also provides good output for bug
reporting.

FAQ on nametrans
----------------

Where to put nametrans rules, on the remote and/or local repository?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

If you never intend to create new folders on the LOCAL repository that
need to be synced to the REMOTE repository, it is sufficient to create a
nametrans rule on the remote Repository section. This will be used to
determine the names of new folder names on the LOCAL repository, and to
match existing folders that correspond.

*IF* you create folders on the local repository, that are supposed to be
 automatically created on the remote repository, you will need to create
 a nametrans rule that provides the reverse name translation.

(A nametrans rule provides only a one-way translation of names and in
order to know which names folders on the LOCAL side would have on the
REMOTE side, you need to specify the reverse nametrans rule on the local
repository)

OfflineImap will complain if it needs to create a new folder on the
remote side and a back-and-forth nametrans-lation does not yield the
original foldername (as that could potentially lead to infinite folder
creation cycles).

What folder separators do I need to use in nametrans rules?
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

**Q:** If I sync from an IMAP server with folder separator '/' to a
  Maildir using the default folder separator '.' which do I need to use
  in nametrans rules?::

      nametrans = lambda f: "INBOX/" + f

  or::
      nametrans = lambda f: "INBOX." + f

**A:** Generally use the folder separator as defined in the repository
  you write the nametrans rule for. That is, use '/' in the above
  case. We will pass in the untranslated name of the IMAP folder as
  parameter (here `f`). The translated name will ultimately have all
  folder separators be replaced with the destination repositories'
  folder separator.

So if 'f' was "Sent", the first nametrans yields the translated name
"INBOX/Sent" to be used on the other side. As that repository uses the
folder separator '.' rather than '/', the ultimate name to be used will
be "INBOX.Sent".

(As a final note, the smart will see that both variants of the above
nametrans rule would have worked identically in this case)

