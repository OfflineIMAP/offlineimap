

Upgrading to 4.0
----------------

If you are upgrading from a version of OfflineIMAP prior to 3.99.12, you will
find that you will get errors when OfflineIMAP starts up (relating to
ConfigParser or AccountHashGenerator) and the configuration file.  This is
because the config file format had to change to accommodate new features in 4.0.
Fortunately, it's not difficult to adjust it to suit.


First thing you need to do is stop any running OfflineIMAP instance, making sure
first that it's synced all your mail.  Then, modify your `~/.offlineimaprc` file.
You'll need to split up each account section (make sure that it now starts with
"Account ") into two Repository sections (one for the local side and another for
the remote side.)  See the files offlineimap.conf.minimal and offlineimap.conf
in the distribution if you need more assistance.


OfflineIMAP's status directory area has also changed.  Therefore, you should
delete everything in `~/.offlineimap` as well as your local mail folders.


When you start up OfflineIMAP 4.0, it will re-download all your mail from the
server and then you can continue using it like normal.
