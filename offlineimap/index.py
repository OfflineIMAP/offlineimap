from subprocess import Popen, PIPE
import shlex

from offlineimap.ui import getglobalui
import offlineimap.accounts

class MessageIndex(object):
    def __init__(self, folder):
        self.folder = folder
        self.ui = getglobalui()

    def add(self, message):
        raise NotImplementedException

    def remove(self, message):
        raise NotImplementedException


class DummyIndex(MessageIndex):

    def add(self, message):
        pass

    def remove(self, message):
        pass


class MemoryIndex(MessageIndex):
    def __init__(self, folder):
        super(MemoryIndex, self).__init__(folder)
        self.data = set()

    def add(self, message):
        self.data.add(message)

    def remove(self, message):
        self.data.remove(message)


class HookIndex(MessageIndex):
    def __init__(self, folder):
        super(HookIndex, self).__init__(folder)
        self.add_command = self.folder.repository.getconf('index_add')
        self.remove_command = self.folder.repository.getconf('index_remove')

    def add(self, message):
        return self.call(self.add_command, message)

    def remove(self, message):
        return self.call(self.remove_command, message)

    def call(self, cmd, message):
        # check for CTRL-C or SIGTERM and run.
        if offlineimap.accounts.Account.abort_NOW_signal.is_set():
            return
        if not cmd:
            return
        cmd_list = shlex.split(cmd)
        cmd_list.append(message)
        cmd = ' '.join(cmd_list)
        p = Popen(cmd_list, shell=False,
                  stdin=PIPE, stdout=PIPE, stderr=PIPE,
                  close_fds=True)
        stdout, stderr = p.communicate()
        self.ui.callhook("Index %s stdout: %s\nHook stderr:%s\n" % (cmd, stdout, stderr))
        self.ui.callhook("Index %s return code: %d" % (cmd, p.returncode))


def message_index_for_backend(backend, account):
    classes = dict(
        memory=MemoryIndex,
        hook=HookIndex,
        dummy=DummyIndex,
    )
    cls = classes.get(backend, None)
    if cls is None:
        raise SyntaxError("unsupported index backend: %s" % backend)
    return cls(account)
