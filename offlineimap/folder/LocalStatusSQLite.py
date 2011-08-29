# Local status cache virtual folder: SQLite backend
# Copyright (C) 2009-2011 Stewart Smith and contributors
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
import os.path
import re
from threading import Lock
from LocalStatus import LocalStatusFolder
try:
    import sqlite3 as sqlite
except:
    pass #fail only if needed later on, not on import

try: # python 2.6 has set() built in
    set
except NameError:
    from sets import Set as set

class LocalStatusSQLiteFolder(LocalStatusFolder):
    """LocalStatus backend implemented with an SQLite database

    As python-sqlite currently does not allow to access the same sqlite
    objects from various threads, we need to open get and close a db
    connection and cursor for all operations. This is a big disadvantage
    and we might want to investigate if we cannot hold an object open
    for a thread somehow."""
    #though. According to sqlite docs, you need to commit() before
    #the connection is closed or your changes will be lost!"""
    #get db connection which autocommits
    #connection = sqlite.connect(self.filename, isolation_level=None)        
    #cursor = connection.cursor()
    #return connection, cursor

    #current version of our db format
    cur_version = 1

    def __init__(self, root, name, repository, accountname, config):
        super(LocalStatusSQLiteFolder, self).__init__(root, name, 
                                                      repository, 
                                                      accountname,
                                                      config)       

        # dblock protects against concurrent writes in same connection
        self._dblock = Lock()
        #Try to establish connection, no need for threadsafety in __init__
        try:
            self.connection = sqlite.connect(self.filename, check_same_thread = False)
        except NameError:
            # sqlite import had failed
            raise UserWarning('SQLite backend chosen, but no sqlite python '
                              'bindings available. Please install.')

        #Make sure sqlite is in multithreading SERIALIZE mode
        assert sqlite.threadsafety == 1, 'Your sqlite is not multithreading safe.'

        #Test if db version is current enough and if db is readable.
        try:
            cursor = self.connection.execute("SELECT value from metadata WHERE key='db_version'")
        except sqlite.DatabaseError:
            #db file missing or corrupt, recreate it.
            self.upgrade_db(0)
        else:
            # fetch db version and upgrade if needed
            version = int(cursor.fetchone()[0])
            if version < LocalStatusSQLiteFolder.cur_version:
                self.upgrade_db(version)

    def sql_write(self, sql, vars=None):
        """execute some SQL retrying if the db was locked.

        :param sql: the SQL string passed to execute() :param args: the
            variable values to `sql`. E.g. (1,2) or {uid:1, flags:'T'}. See
            sqlite docs for possibilities.
        :returns: the Cursor() or raises an Exception"""
        success = False
        while not success:
            self._dblock.acquire()
            try:
                if vars is None:
                    cursor = self.connection.execute(sql)
                else:
                    cursor = self.connection.execute(sql, vars)
                success = True
                self.connection.commit()
            except sqlite.OperationalError, e:
                if e.args[0] == 'cannot commit - no transaction is active':
                    pass
                elif e.args[0] == 'database is locked':
                    self.ui.debug('', "Locked sqlite database, retrying.")
                    success = False
                else:
                    raise
            finally:
                self._dblock.release()
        return cursor

    def upgrade_db(self, from_ver):
        """Upgrade the sqlite format from version 'from_ver' to current"""

        if hasattr(self, 'connection'):
            self.connection.close() #close old connections first
        self.connection = sqlite.connect(self.filename,
                                         check_same_thread = False)

        if from_ver == 0:
            # from_ver==0: no db existent: plain text migration?
            self.create_db()
            # below was derived from repository.getfolderfilename() logic
            plaintextfilename = os.path.join(
                self.repository.account.getaccountmeta(),
                'LocalStatus',
                self.getfolderbasename())
            # MIGRATE from plaintext if needed
            if os.path.exists(plaintextfilename):
                self.ui._msg('Migrating LocalStatus cache from plain text '
                             'to sqlite database for %s:%s' %\
                                 (self.repository, self))
                file = open(plaintextfilename, "rt")
                line = file.readline().strip()
                data = []
                for line in file.xreadlines():
                    uid, flags = line.strip().split(':')
                    uid = long(uid)
                    flags = ''.join(sorted(flags))
                    data.append((uid,flags))
                self.connection.executemany('INSERT INTO status (id,flags) VALUES (?,?)',
                                       data)
                self.connection.commit()
                file.close()
                os.rename(plaintextfilename, plaintextfilename + ".old")
        # Future version upgrades come here...
        # if from_ver <= 1: ... #upgrade from 1 to 2
        # if from_ver <= 2: ... #upgrade from 2 to 3

    def create_db(self):
        """Create a new db file"""
        self.ui._msg('Creating new Local Status db for %s:%s' \
                         % (self.repository, self))
        if hasattr(self, 'connection'):
            self.connection.close() #close old connections first
        self.connection = sqlite.connect(self.filename, check_same_thread = False)
        self.connection.executescript("""
        CREATE TABLE metadata (key VARCHAR(50) PRIMARY KEY, value VARCHAR(128));
        INSERT INTO metadata VALUES('db_version', '1');
        CREATE TABLE status (id INTEGER PRIMARY KEY, flags VARCHAR(50));
        """)
        self.connection.commit()

    def isnewfolder(self):
        # testing the existence of the db file won't work. It is created
        # as soon as this class instance was intitiated. So say it is a
        # new folder when there are no messages at all recorded in it.
        return self.getmessagecount() > 0

    def deletemessagelist(self):
        """delete all messages in the db"""
        self.sql_write('DELETE FROM status')

    def cachemessagelist(self):
        self.messagelist = {}
        cursor = self.connection.execute('SELECT id,flags from status')
        for row in cursor:
                flags = set(row[1])
                self.messagelist[row[0]] = {'uid': row[0], 'flags': flags}

    def save(self):
        #Noop in this backend
        pass

    # Following some pure SQLite functions, where we chose to use
    # BaseFolder() methods instead. Doing those on the in-memory list is
    # quicker anyway. If our db becomes so big that we don't want to
    # maintain the in-memory list anymore, these might come in handy
    # in the future though.
    #
    #def uidexists(self,uid):
    #    conn, cursor = self.get_cursor()
    #    with conn:
    #        cursor.execute('SELECT id FROM status WHERE id=:id',{'id': uid})
    #        return cursor.fetchone()
    # This would be the pure SQLite solution, use BaseFolder() method,
    # to avoid threading with sqlite...
    #def getmessageuidlist(self):
    #    conn, cursor = self.get_cursor()
    #    with conn:
    #        cursor.execute('SELECT id from status')
    #        r = []
    #        for row in cursor:
    #            r.append(row[0])
    #        return r
    #def getmessagecount(self):
    #    conn, cursor = self.get_cursor()
    #    with conn:
    #        cursor.execute('SELECT count(id) from status');
    #        return cursor.fetchone()[0]
    #def getmessageflags(self, uid):
    #    conn, cursor = self.get_cursor()
    #    with conn:
    #        cursor.execute('SELECT flags FROM status WHERE id=:id',
    #                        {'id': uid})
    #        for row in cursor:
    #            flags = [x for x in row[0]]
    #            return flags
    #        assert False,"getmessageflags() called on non-existing message"

    def savemessage(self, uid, content, flags, rtime):
        if uid < 0:
            # We cannot assign a uid.
            return uid

        if self.uidexists(uid):     # already have it
            self.savemessageflags(uid, flags)
            return uid

        self.messagelist[uid] = {'uid': uid, 'flags': flags, 'time': rtime}
        flags = ''.join(sorted(flags))
        self.sql_write('INSERT INTO status (id,flags) VALUES (?,?)',
                         (uid,flags))
        return uid

    def savemessageflags(self, uid, flags):
        self.messagelist[uid] = {'uid': uid, 'flags': flags}
        flags = ''.join(sorted(flags))
        self.sql_write('UPDATE status SET flags=? WHERE id=?',(flags,uid))

    def deletemessages(self, uidlist):
        # Weed out ones not in self.messagelist
        uidlist = [uid for uid in uidlist if uid in self.messagelist]
        if not len(uidlist):
            return
        for uid in uidlist:
            del(self.messagelist[uid])
            #TODO: we want a way to do executemany(.., uidlist) to delete all
            self.sql_write('DELETE FROM status WHERE id=?', (uid, ))
