The offlineimap 'binary' command line options
=============================================

Offlineimap is invoked with the following pattern: `offlineimap [args...]`.

Where [args...] are as follows:

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -1                    Disable all multithreading operations and use solely a
                        single-thread sync. This effectively sets the
                        maxsyncaccounts and all maxconnections configuration
                        file variables to 1.
  -P DIR                Sets OfflineIMAP into profile mode. The program will
                        create DIR (it must not already exist). As it runs,
                        Python profiling information about each thread is
                        logged into profiledir. Please note: This option is
                        present for debugging and optimization only, and
                        should NOT be used unless you have a specific reason
                        to do so. It will significantly slow program
                        performance, may reduce reliability, and can generate
                        huge amounts of  data. This option implies the
                        singlethreading option (-1).
  -a ACCOUNTS           Overrides the accounts section in the config file.
                        Lets you specify a particular account or set of
                        accounts to sync without having to edit the config
                        file. You might use this to exclude certain accounts,
                        or to sync some accounts that you normally prefer not
                        to.
  -c FILE               Specifies a configuration file to use in lieu of
                        ~/.offlineimaprc.

  -d type1,[type2...]   Enables debugging for OfflineIMAP.  This is useful if
                        you are trying to track down a malfunction or figure
                        out what is going on under the hood.  I suggest that
                        you use this with -1 in order to make the results more
                        sensible. This option requires one or more debugtypes,
                        separated by commas. These define what exactly  will
                        be debugged, and so far include the options: imap,
                        thread,maildir or ALL.  The imap option will enable
                        IMAP protocol stream and parsing debugging.  Note that
                        the output may contain passwords, so take care to
                        remove  that from the debugging output before sending
                        it to anyone else. The maildir option will enable
                        debugging for certain Maildir operations.

  -l FILE               Log to FILE

  -f folder1,[folder2...]
                        Only sync the specified folders. The 'folder's are the
                        *untranslated* foldernames. This command-line option
                        overrides any 'folderfilter' and 'folderincludes'
                        options in the configuration file.

  -k `[section:]option=value`
                        Override configuration file option.  If"section" is
                        omitted, it defaults to "general".  Any underscores
                        "_" in the section name are replaced with spaces:
                        for instance, to override option "autorefresh" in
                        the "[Account Personal]" section in the config file
                        one would use "-k Account_Personal:autorefresh=30".

  -o                    Run only once, ignoring any autorefresh setting in the
                        configuration file.
  -q                    Run only quick synchronizations. Ignore any flag
                        updates on IMAP servers.
  -u INTERFACE          Specifies an alternative user interface to use. This
                        overrides the default specified in the configuration
                        file. The UI specified with -u  will be forced to be
                        used, even if checks determine that it is not usable.
                        Possible interface choices are: Curses.Blinkenlights,
                        TTY.TTYUI, Noninteractive.Basic, Noninteractive.Quiet,
                        Machine.MachineUI



Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

