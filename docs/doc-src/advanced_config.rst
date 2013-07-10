Message filtering
=================

There are two ways to selectively filter messages out of a folder, using `maxsize` and `maxage`. Setting each option will basically ignore all messages that are on the server by pretending they don't exist.

:todo: explain them and give tipps on how to use and not use them. Use cases!

maxage
------

:todo: !

maxsize
-------

:todo: !


Message date fixing
===================

By default, synchronizing from an IMAP folder to a local Maildir does not map the messages time to the local file's timestamp. By using the `syncdate` option, the files' timestamp in the Maildir will be
changed to match the Received date of each message.

syncdate
--------

By default, set to False.  Changing to True makes OfflineImap change the files's timestamp in the Maildir to match the 'Received' header of the message 
