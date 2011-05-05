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
from LocalStatus import LocalStatusFolder, magicline
try:
    from pysqlite2 import dbapi2 as sqlite
except:
    pass #fail only if needed later on, not on import

class LocalStatusSQLiteFolder(LocalStatusFolder):
    """LocalStatus backend implemented with an SQLite database"""
    #current version of the db format
    cur_version = 1

    def __init__(self, root, name, repository, accountname, config):
        super(LocalStatusSQLiteFolder, self).__init__(root, name, 
                                                      repository, 
                                                      accountname,
                                                      config)       
        #Try to establish connection
        try:
            self.connection = sqlite.connect(self.filename)
        except NameError:
            # sqlite import had failed
            raise UserWarning('SQLite backend chosen, but no sqlite python '
                              'bindings available. Please install.')

        #Test if the db version is current enough and if the db is
        #readable.
        try:
            self.cursor = self.connection.cursor()
            self.cursor.execute("SELECT value from metadata WHERE key='db_version'")
        except sqlite.DatabaseError:
            #db file missing or corrupt, recreate it.
            self.connection.close()
            self.upgrade_db(0)
        else:
            # fetch db version and upgrade if needed
            version = int(self.cursor.fetchone()[0])
            self.cursor.close()
            if version < LocalStatusSQLiteFolder.cur_version:
                self.upgrade_db(version)
            self.connection.close()

    def upgrade_db(self, from_ver):
        """Upgrade the sqlite format from version 'from_ver' to current"""
        if from_ver == 0:
            # from_ver==0: no db existent: plain text migration?
            self.create_db()
            # below was derived from repository.getfolderfilename() logic
            plaintextfilename = os.path.join(
                self.repository.account.getaccountmeta(),
                'LocalStatus',
                re.sub('(^|\/)\.$','\\1dot', self.name))
            # MIGRATE from plaintext if needed
            if os.path.exists(plaintextfilename):
                self.ui._msg('Migrating LocalStatus cache from plain text '
                             'to sqlite database for %s:%s' %\
                                 (self.repository, self))
                file = open(plaintextfilename, "rt")
                line = file.readline().strip()
                assert(line == magicline)
                connection = sqlite.connect(self.filename)
                cursor = connection.cursor()
                for line in file.xreadlines():
                    line = line.strip()
                    uid, flags = line.split(':')
                    uid = long(uid)
                    flags = [x for x in flags]
                    flags.sort()
                    flags = ''.join(flags)
                    self.cursor.execute('INSERT INTO status (id,flags) VALUES (?,?)',
                                        (uid,flags))
                file.close()
                self.connection.commit()
                os.rename(plaintextfilename, plaintextfilename + ".old")
                self.connection.close()
        # Future version upgrades come here...
        # if from_ver <= 1: ... #upgrade from 1 to 2
        # if from_ver <= 2: ... #upgrade from 2 to 3

    def create_db(self):
        """Create a new db file"""
        self.ui._msg('Creating new Local Status db for %s:%s' \
                         % (self.repository, self))
        connection = sqlite.connect(self.filename)
        cursor = connection.cursor()
        cursor.execute('CREATE TABLE metadata (key VARCHAR(50) PRIMARY KEY, value VARCHAR(128))')
        cursor.execute("INSERT INTO metadata VALUES('db_version', '1')")
        cursor.execute('CREATE TABLE status (id INTEGER PRIMARY KEY, flags VARCHAR(50))')
        self.autosave() #commit if needed

    def isnewfolder(self):
        # testing the existence of the db file won't work. It is created
        # as soon as this class instance was intitiated. So say it is a
        # new folder when there are no messages at all recorded in it.
        return self.getmessagecount() > 0

    def deletemessagelist(self):
        """delete all messages in the db"""
        self.cursor.execute('DELETE FROM status')

    def cachemessagelist(self):
        self.messagelist = {}
        self.cursor.execute('SELECT id,flags from status')
        for row in self.cursor:
            flags = [x for x in row[1]]
            self.messagelist[row[0]] = {'uid': row[0], 'flags': flags}

    def save(self):
        #Noop in this backend
        pass

    def uidexists(self,uid):
        self.cursor.execute('SELECT id FROM status WHERE id=:id',{'id': uid})
        for row in self.cursor:
            if(row[0]==uid):
                return 1
        return 0

    def getmessageuidlist(self):
        self.cursor.execute('SELECT id from status')
        r = []
        for row in self.cursor:
            r.append(row[0])
        return r

    def getmessagecount(self):
        self.cursor.execute('SELECT count(id) from status');
        row = self.cursor.fetchone()
        return row[0]

    def savemessage(self, uid, content, flags, rtime):
        if uid < 0:
            # We cannot assign a uid.
            return uid

        if self.uidexists(uid):     # already have it
            self.savemessageflags(uid, flags)
            return uid

        self.messagelist[uid] = {'uid': uid, 'flags': flags, 'time': rtime}
        flags.sort()
        flags = ''.join(flags)
        self.cursor.execute('INSERT INTO status (id,flags) VALUES (?,?)',
                            (uid,flags))
        self.autosave()
        return uid

    def getmessageflags(self, uid):
        self.cursor.execute('SELECT flags FROM status WHERE id=:id',
                            {'id': uid})
        for row in self.cursor:
            flags = [x for x in row[0]]
            return flags
        assert False,"getmessageflags() called on non-existing message"

    def getmessagetime(self, uid):
        return self.messagelist[uid]['time']

    def savemessageflags(self, uid, flags):
        self.messagelist[uid] = {'uid': uid, 'flags': flags}
        flags.sort()
        flags = ''.join(flags)
        self.cursor.execute('UPDATE status SET flags=? WHERE id=?',(flags,uid))
        self.autosave()

    def deletemessages(self, uidlist):
        # Weed out ones not in self.messagelist
        uidlist = [uid for uid in uidlist if uid in self.messagelist]
        if not len(uidlist):
            return

        for uid in uidlist:
            del(self.messagelist[uid])
            #if self.uidexists(uid):
            self.cursor.execute('DELETE FROM status WHERE id=:id', {'id': uid})
