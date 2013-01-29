Message filtering
=================

There are several ways to selectively filter messages out of a folder. Setting one of these options will effectively ignore all messages that are on the server that don't fall into the filter range by pretending they don't exist.

:todo: explain them and give tipps on how to use and not use them. Use cases!

maxage
------
Integer value. Will ignore all messages older than 'maxage' days old

startdate
---------
Date in the form "YYYY-MM-DD". Will ignore all messages older than the specified date

Example: startdate = 2012-10-01

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
