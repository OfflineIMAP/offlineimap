#!/usr/bin/env python

"""Threaded IMAP4 client.

Based on RFC 3501 and original imaplib module.

Public classes:   IMAP4
                  IMAP4_SSL
                  IMAP4_stream

Public functions: Internaldate2Time
                  ParseFlags
                  Time2Internaldate
"""


__all__ = ("IMAP4", "IMAP4_SSL", "IMAP4_stream",
           "Internaldate2Time", "ParseFlags", "Time2Internaldate")

__version__ = "2.52"
__release__ = "2"
__revision__ = "52"
__credits__ = """
Authentication code contributed by Donn Cave <donn@u.washington.edu> June 1998.
String method conversion by ESR, February 2001.
GET/SETACL contributed by Anthony Baxter <anthony@interlink.com.au> April 2001.
IMAP4_SSL contributed by Tino Lange <Tino.Lange@isg.de> March 2002.
GET/SETQUOTA contributed by Andreas Zeidler <az@kreativkombinat.de> June 2002.
PROXYAUTH contributed by Rick Holbert <holbert.13@osu.edu> November 2002.
IDLE via threads suggested by Philippe Normand <phil@respyre.org> January 2005.
GET/SETANNOTATION contributed by Tomas Lindroos <skitta@abo.fi> June 2005.
COMPRESS/DEFLATE contributed by Bron Gondwana <brong@brong.net> May 2009.
STARTTLS from Jython's imaplib by Alan Kennedy.
ID contributed by Dave Baggett <dave@baggett.org> November 2009.
Improved untagged responses handling suggested by Dave Baggett <dave@baggett.org> November 2009.
Improved thread naming, and 0 read detection contributed by Grant Edwards <grant.b.edwards@gmail.com> June 2010.
Improved timeout handling contributed by Ivan Vovnenko <ivovnenko@gmail.com> October 2010.
Timeout handling further improved by Ethan Glasser-Camp <glasse@cs.rpi.edu> December 2010.
Time2Internaldate() patch to match RFC2060 specification of English month names from bugs.python.org/issue11024 March 2011.
starttls() bug fixed with the help of Sebastian Spaeth <sebastian@sspaeth.de> April 2011.
Threads now set the "daemon" flag (suggested by offlineimap-project) April 2011.
Single quoting introduced with the help of Vladimir Marek <vladimir.marek@oracle.com> August 2011.
Support for specifying SSL version by Ryan Kavanagh <rak@debian.org> July 2013.
Fix for gmail "read 0" error provided by Jim Greenleaf <james.a.greenleaf@gmail.com> August 2013.
Fix for offlineimap "indexerror: string index out of range" bug provided by Eygene Ryabinkin <rea@codelabs.ru> August 2013.
Fix for missing idle_lock in _handler() provided by Franklin Brook <franklin@brook.se> August 2014.
Conversion to Python3 provided by F. Malina <fmalina@gmail.com> February 2015.
Fix for READ-ONLY error from multiple EXAMINE/SELECT calls by Pierre-Louis Bonicoli <pierre-louis.bonicoli@gmx.fr> March 2015.
Fix for null strings appended to untagged responses by Pierre-Louis Bonicoli <pierre-louis.bonicoli@gmx.fr> March 2015.
Fix for correct byte encoding for _CRAM_MD5_AUTH taken from python3.5 imaplib.py June 2015.
Fix for correct Python 3 exception handling by Tobias Brink <tobias.brink@gmail.com> August 2015.
Fix to allow interruptible IDLE command by Tim Peoples <dromedary512@users.sf.net> September 2015.
Add support for TLS levels by Ben Boeckel <mathstuf@gmail.com> September 2015.
Fix for shutown exception by Sebastien Gross <seb@chezwam.org> November 2015."""
__author__ = "Piers Lauder <piers@janeelix.com>"
__URL__ = "http://imaplib2.sourceforge.net"
__license__ = "Python License"

import binascii, errno, os, random, re, select, socket, sys, time, threading, zlib

if bytes != str:
    # Python 3, but NB assumes strings in all I/O
    # for backwards compatibility with python 2 usage.
    import queue
    string_types = str
else:
    import Queue as queue
    string_types = basestring
    threading.TIMEOUT_MAX = 9223372036854.0

select_module = select

#       Globals

CRLF = '\r\n'
Debug = None                                    # Backward compatibility
IMAP4_PORT = 143
IMAP4_SSL_PORT = 993

IDLE_TIMEOUT_RESPONSE = '* IDLE TIMEOUT\r\n'
IDLE_TIMEOUT = 60*29                            # Don't stay in IDLE state longer
READ_POLL_TIMEOUT = 30                          # Without this timeout interrupted network connections can hang reader
READ_SIZE = 32768                               # Consume all available in socket

DFLT_DEBUG_BUF_LVL = 3                          # Level above which the logging output goes directly to stderr

TLS_SECURE = "tls_secure"                       # Recognised TLS levels
TLS_NO_SSL = "tls_no_ssl"
TLS_COMPAT = "tls_compat"

AllowedVersions = ('IMAP4REV1', 'IMAP4')        # Most recent first

#       Commands

CMD_VAL_STATES = 0
CMD_VAL_ASYNC = 1
NONAUTH, AUTH, SELECTED, LOGOUT = 'NONAUTH', 'AUTH', 'SELECTED', 'LOGOUT'

Commands = {
        # name            valid states             asynchronous
        'APPEND':       ((AUTH, SELECTED),            False),
        'AUTHENTICATE': ((NONAUTH,),                  False),
        'CAPABILITY':   ((NONAUTH, AUTH, SELECTED),   True),
        'CHECK':        ((SELECTED,),                 True),
        'CLOSE':        ((SELECTED,),                 False),
        'COMPRESS':     ((AUTH,),                     False),
        'COPY':         ((SELECTED,),                 True),
        'CREATE':       ((AUTH, SELECTED),            True),
        'DELETE':       ((AUTH, SELECTED),            True),
        'DELETEACL':    ((AUTH, SELECTED),            True),
        'EXAMINE':      ((AUTH, SELECTED),            False),
        'EXPUNGE':      ((SELECTED,),                 True),
        'FETCH':        ((SELECTED,),                 True),
        'GETACL':       ((AUTH, SELECTED),            True),
        'GETANNOTATION':((AUTH, SELECTED),            True),
        'GETQUOTA':     ((AUTH, SELECTED),            True),
        'GETQUOTAROOT': ((AUTH, SELECTED),            True),
        'ID':           ((NONAUTH, AUTH, LOGOUT, SELECTED),   True),
        'IDLE':         ((SELECTED,),                 False),
        'LIST':         ((AUTH, SELECTED),            True),
        'LOGIN':        ((NONAUTH,),                  False),
        'LOGOUT':       ((NONAUTH, AUTH, LOGOUT, SELECTED),   False),
        'LSUB':         ((AUTH, SELECTED),            True),
        'MYRIGHTS':     ((AUTH, SELECTED),            True),
        'NAMESPACE':    ((AUTH, SELECTED),            True),
        'NOOP':         ((NONAUTH, AUTH, SELECTED),   True),
        'PARTIAL':      ((SELECTED,),                 True),
        'PROXYAUTH':    ((AUTH,),                     False),
        'RENAME':       ((AUTH, SELECTED),            True),
        'SEARCH':       ((SELECTED,),                 True),
        'SELECT':       ((AUTH, SELECTED),            False),
        'SETACL':       ((AUTH, SELECTED),            False),
        'SETANNOTATION':((AUTH, SELECTED),            True),
        'SETQUOTA':     ((AUTH, SELECTED),            False),
        'SORT':         ((SELECTED,),                 True),
        'STARTTLS':     ((NONAUTH,),                  False),
        'STATUS':       ((AUTH, SELECTED),            True),
        'STORE':        ((SELECTED,),                 True),
        'SUBSCRIBE':    ((AUTH, SELECTED),            False),
        'THREAD':       ((SELECTED,),                 True),
        'UID':          ((SELECTED,),                 True),
        'UNSUBSCRIBE':  ((AUTH, SELECTED),            False),
        }

UID_direct = ('SEARCH', 'SORT', 'THREAD')


def Int2AP(num):

    """string = Int2AP(num)
    Return 'num' converted to a string using characters from the set 'A'..'P'
    """

    val, a2p = [], 'ABCDEFGHIJKLMNOP'
    num = int(abs(num))
    while num:
        num, mod = divmod(num, 16)
        val.insert(0, a2p[mod])
    return ''.join(val)



class Request(object):

    """Private class to represent a request awaiting response."""

    def __init__(self, parent, name=None, callback=None, cb_arg=None, cb_self=False):
        self.parent = parent
        self.name = name
        self.callback = callback               # Function called to process result
        if not cb_self:
            self.callback_arg = cb_arg         # Optional arg passed to "callback"
        else:
            self.callback_arg = (self, cb_arg) # Self reference required in callback arg

        self.tag = '%s%s' % (parent.tagpre, parent.tagnum)
        parent.tagnum += 1

        self.ready = threading.Event()
        self.response = None
        self.aborted = None
        self.data = None


    def abort(self, typ, val):
        self.aborted = (typ, val)
        self.deliver(None)


    def get_response(self, exc_fmt=None):
        self.callback = None
        if __debug__: self.parent._log(3, '%s:%s.ready.wait' % (self.name, self.tag))
        self.ready.wait(threading.TIMEOUT_MAX)

        if self.aborted is not None:
            typ, val = self.aborted
            if exc_fmt is None:
                exc_fmt = '%s - %%s' % typ
            raise typ(exc_fmt % str(val))

        return self.response


    def deliver(self, response):
        if self.callback is not None:
            self.callback((response, self.callback_arg, self.aborted))
            return

        self.response = response
        self.ready.set()
        if __debug__: self.parent._log(3, '%s:%s.ready.set' % (self.name, self.tag))




class IMAP4(object):

    """Threaded IMAP4 client class.

    Instantiate with:
        IMAP4(host=None, port=None, debug=None, debug_file=None, identifier=None, timeout=None, debug_buf_lvl=None)

        host          - host's name (default: localhost);
        port          - port number (default: standard IMAP4 port);
        debug         - debug level (default: 0 - no debug);
        debug_file    - debug stream (default: sys.stderr);
        identifier    - thread identifier prefix (default: host);
        timeout       - timeout in seconds when expecting a command response (default: no timeout),
        debug_buf_lvl - debug level at which buffering is turned off.

    All IMAP4rev1 commands are supported by methods of the same name.

    Each command returns a tuple: (type, [data, ...]) where 'type'
    is usually 'OK' or 'NO', and 'data' is either the text from the
    tagged response, or untagged results from command. Each 'data' is
    either a string, or a tuple. If a tuple, then the first part is the
    header of the response, and the second part contains the data (ie:
    'literal' value).

    Errors raise the exception class <instance>.error("<reason>").
    IMAP4 server errors raise <instance>.abort("<reason>"), which is
    a sub-class of 'error'. Mailbox status changes from READ-WRITE to
    READ-ONLY raise the exception class <instance>.readonly("<reason>"),
    which is a sub-class of 'abort'.

    "error" exceptions imply a program error.
    "abort" exceptions imply the connection should be reset, and
            the command re-tried.
    "readonly" exceptions imply the command should be re-tried.

    All commands take two optional named arguments:
        'callback' and 'cb_arg'
    If 'callback' is provided then the command is asynchronous, so after
    the command is queued for transmission, the call returns immediately
    with the tuple (None, None).
    The result will be posted by invoking "callback" with one arg, a tuple:
        callback((result, cb_arg, None))
    or, if there was a problem:
        callback((None, cb_arg, (exception class, reason)))

    Otherwise the command is synchronous (waits for result). But note
    that state-changing commands will both block until previous commands
    have completed, and block subsequent commands until they have finished.

    All (non-callback) arguments to commands are converted to strings,
    except for AUTHENTICATE, and the last argument to APPEND which is
    passed as an IMAP4 literal.  If necessary (the string contains any
    non-printing characters or white-space and isn't enclosed with
    either parentheses or double or single quotes) each string is
    quoted.  However, the 'password' argument to the LOGIN command is
    always quoted.  If you want to avoid having an argument string
    quoted (eg: the 'flags' argument to STORE) then enclose the string
    in parentheses (eg: "(\Deleted)"). If you are using "sequence sets"
    containing the wildcard character '*', then enclose the argument
    in single quotes: the quotes will be removed and the resulting
    string passed unquoted. Note also that you can pass in an argument
    with a type that doesn't evaluate to 'string_types' (eg: 'bytearray')
    and it will be converted to a string without quoting.

    There is one instance variable, 'state', that is useful for tracking
    whether the client needs to login to the server. If it has the
    value "AUTH" after instantiating the class, then the connection
    is pre-authenticated (otherwise it will be "NONAUTH"). Selecting a
    mailbox changes the state to be "SELECTED", closing a mailbox changes
    back to "AUTH", and once the client has logged out, the state changes
    to "LOGOUT" and no further commands may be issued.

    Note: to use this module, you must read the RFCs pertaining to the
    IMAP4 protocol, as the semantics of the arguments to each IMAP4
    command are left to the invoker, not to mention the results. Also,
    most IMAP servers implement a sub-set of the commands available here.

    Note also that you must call logout() to shut down threads before
    discarding an instance.
    """

    class error(Exception): pass    # Logical errors - debug required
    class abort(error): pass        # Service errors - close and retry
    class readonly(abort): pass     # Mailbox status changed to READ-ONLY


    continuation_cre = re.compile(r'\+( (?P<data>.*))?')
    literal_cre = re.compile(r'.*{(?P<size>\d+)}$')
    mapCRLF_cre = re.compile(r'\r\n|\r|\n')
        # Need to quote "atom-specials" :-
        #   "(" / ")" / "{" / SP / 0x00 - 0x1f / 0x7f / "%" / "*" / DQUOTE / "\" / "]"
        # so match not the inverse set
    mustquote_cre = re.compile(r"[^!#$&'+,./0-9:;<=>?@A-Z\[^_`a-z|}~-]")
    response_code_cre = re.compile(r'\[(?P<type>[A-Z-]+)( (?P<data>[^\]]*))?\]')
    # sequence_set_cre = re.compile(r"^[0-9]+(:([0-9]+|\*))?(,[0-9]+(:([0-9]+|\*))?)*$")
    untagged_response_cre = re.compile(r'\* (?P<type>[A-Z-]+)( (?P<data>.*))?')
    untagged_status_cre = re.compile(r'\* (?P<data>\d+) (?P<type>[A-Z-]+)( (?P<data2>.*))?')


    def __init__(self, host=None, port=None, debug=None, debug_file=None, identifier=None, timeout=None, debug_buf_lvl=None):

        self.state = NONAUTH            # IMAP4 protocol state
        self.literal = None             # A literal argument to a command
        self.tagged_commands = {}       # Tagged commands awaiting response
        self.untagged_responses = []    # [[typ: [data, ...]], ...]
        self.mailbox = None             # Current mailbox selected
        self.is_readonly = False        # READ-ONLY desired state
        self.idle_rqb = None            # Server IDLE Request - see _IdleCont
        self.idle_timeout = None        # Must prod server occasionally

        self._expecting_data = False    # Expecting message data
        self._expecting_data_len = 0    # How many characters we expect
        self._accumulated_data = []     # Message data accumulated so far
        self._literal_expected = None   # Message data descriptor

        self.compressor = None          # COMPRESS/DEFLATE if not None
        self.decompressor = None
        self._tls_established = False

        # Create unique tag for this session,
        # and compile tagged response matcher.

        self.tagnum = 0
        self.tagpre = Int2AP(random.randint(4096, 65535))
        self.tagre = re.compile(r'(?P<tag>'
                        + self.tagpre
                        + r'\d+) (?P<type>[A-Z]+) (?P<data>.*)')

        if __debug__: self._init_debug(debug, debug_file, debug_buf_lvl)

        self.resp_timeout = timeout     # Timeout waiting for command response

        if timeout is not None and timeout < READ_POLL_TIMEOUT:
            self.read_poll_timeout = timeout
        else:
            self.read_poll_timeout = READ_POLL_TIMEOUT
        self.read_size = READ_SIZE

        # Open socket to server.

        self.open(host, port)

        if __debug__:
            if debug:
                self._mesg('connected to %s on port %s' % (self.host, self.port))

        # Threading

        if identifier is not None:
            self.identifier = identifier
        else:
            self.identifier = self.host
        if self.identifier:
            self.identifier += ' '

        self.Terminate = self.TerminateReader = False

        self.state_change_free = threading.Event()
        self.state_change_pending = threading.Lock()
        self.commands_lock = threading.Lock()
        self.idle_lock = threading.Lock()

        self.ouq = queue.Queue(10)
        self.inq = queue.Queue()

        self.wrth = threading.Thread(target=self._writer)
        self.wrth.setDaemon(True)
        self.wrth.start()
        self.rdth = threading.Thread(target=self._reader)
        self.rdth.setDaemon(True)
        self.rdth.start()
        self.inth = threading.Thread(target=self._handler)
        self.inth.setDaemon(True)
        self.inth.start()

        # Get server welcome message,
        # request and store CAPABILITY response.

        try:
            self.welcome = self._request_push(name='welcome', tag='continuation').get_response('IMAP4 protocol error: %s')[1]

            if self._get_untagged_response('PREAUTH'):
                self.state = AUTH
                if __debug__: self._log(1, 'state => AUTH')
            elif self._get_untagged_response('OK'):
                if __debug__: self._log(1, 'state => NONAUTH')
            else:
                raise self.error('unrecognised server welcome message: %s' % repr(self.welcome))

            typ, dat = self.capability()
            if dat == [None]:
                raise self.error('no CAPABILITY response from server')
            self.capabilities = tuple(dat[-1].upper().split())
            if __debug__: self._log(1, 'CAPABILITY: %r' % (self.capabilities,))

            for version in AllowedVersions:
                if not version in self.capabilities:
                    continue
                self.PROTOCOL_VERSION = version
                break
            else:
                raise self.error('server not IMAP4 compliant')
        except:
            self._close_threads()
            raise


    def __getattr__(self, attr):
        # Allow UPPERCASE variants of IMAP4 command methods.
        if attr in Commands:
            return getattr(self, attr.lower())
        raise AttributeError("Unknown IMAP4 command: '%s'" % attr)



    #       Overridable methods


    def open(self, host=None, port=None):
        """open(host=None, port=None)
        Setup connection to remote server on "host:port"
            (default: localhost:standard IMAP4 port).
        This connection will be used by the routines:
            read, send, shutdown, socket."""

        self.host = self._choose_nonull_or_dflt('', host)
        self.port = self._choose_nonull_or_dflt(IMAP4_PORT, port)
        self.sock = self.open_socket()
        self.read_fd = self.sock.fileno()


    def open_socket(self):
        """open_socket()
        Open socket choosing first address family available."""

        msg = (-1, 'could not open socket')
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
            except socket.error as m:
                msg = m
                continue
            try:
                for i in (0, 1):
                    try:
                        s.connect(sa)
                        break
                    except socket.error as m:
                        msg = m
                        if len(msg.args) < 2 or msg.args[0] != errno.EINTR:
                            raise
                else:
                    raise socket.error(msg)
            except socket.error as m:
                msg = m
                s.close()
                continue
            break
        else:
            raise socket.error(msg)

        return s


    def ssl_wrap_socket(self):

        try:
            import ssl

            TLS_MAP = {}
            if hasattr(ssl, "PROTOCOL_TLSv1_2"):        # py3
                TLS_MAP[TLS_SECURE] = {
                    "tls1_2": ssl.PROTOCOL_TLSv1_2,
                    "tls1_1": ssl.PROTOCOL_TLSv1_1,
                }
            else:
                TLS_MAP[TLS_SECURE] = {}
            TLS_MAP[TLS_NO_SSL] = TLS_MAP[TLS_SECURE].copy()
            TLS_MAP[TLS_NO_SSL].update({
                "tls1": ssl.PROTOCOL_TLSv1,
            })
            TLS_MAP[TLS_COMPAT] = TLS_MAP[TLS_NO_SSL].copy()
            TLS_MAP[TLS_COMPAT].update({
                "ssl23": ssl.PROTOCOL_SSLv23,
                None: ssl.PROTOCOL_SSLv23,
            })
            if hasattr(ssl, "PROTOCOL_SSLv3"):          # Might not be available.
                TLS_MAP[TLS_COMPAT].update({
                    "ssl3": ssl.PROTOCOL_SSLv3
                })

            if self.ca_certs is not None:
                cert_reqs = ssl.CERT_REQUIRED
            else:
                cert_reqs = ssl.CERT_NONE

            if self.tls_level not in TLS_MAP:
                raise RuntimeError("unknown tls_level: %s" % self.tls_level)

            if self.ssl_version not in TLS_MAP[self.tls_level]:
                raise socket.sslerror("Invalid SSL version '%s' requested for tls_version '%s'" % (self.ssl_version, self.tls_level))

            ssl_version =  TLS_MAP[self.tls_level][self.ssl_version]

            self.sock = ssl.wrap_socket(self.sock, self.keyfile, self.certfile, ca_certs=self.ca_certs, cert_reqs=cert_reqs, ssl_version=ssl_version)
            ssl_exc = ssl.SSLError
            self.read_fd = self.sock.fileno()
        except ImportError:
            # No ssl module, and socket.ssl has no fileno(), and does not allow certificate verification
            raise socket.sslerror("imaplib SSL mode does not work without ssl module")

        if self.cert_verify_cb is not None:
            cert_err = self.cert_verify_cb(self.sock.getpeercert(), self.host)
            if cert_err:
                raise ssl_exc(cert_err)

        # Allow sending of keep-alive messages - seems to prevent some servers
        # from closing SSL, leading to deadlocks.
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)



    def start_compressing(self):
        """start_compressing()
        Enable deflate compression on the socket (RFC 4978)."""

        # rfc 1951 - pure DEFLATE, so use -15 for both windows
        self.decompressor = zlib.decompressobj(-15)
        self.compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)


    def read(self, size):
        """data = read(size)
        Read at most 'size' bytes from remote."""

        if self.decompressor is None:
            return self.sock.recv(size)

        if self.decompressor.unconsumed_tail:
            data = self.decompressor.unconsumed_tail
        else:
            data = self.sock.recv(READ_SIZE)

        return self.decompressor.decompress(data, size)


    def send(self, data):
        """send(data)
        Send 'data' to remote."""

        if self.compressor is not None:
            data = self.compressor.compress(data)
            data += self.compressor.flush(zlib.Z_SYNC_FLUSH)

        if bytes != str:
            data = bytes(data, 'ASCII')

        self.sock.sendall(data)


    def shutdown(self):
        """shutdown()
        Close I/O established in "open"."""

        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            # The server might already have closed the connection
            if e.errno != errno.ENOTCONN:
                raise
        finally:
            self.sock.close()


    def socket(self):
        """socket = socket()
        Return socket instance used to connect to IMAP4 server."""

        return self.sock



    #       Utility methods


    def enable_compression(self):
        """enable_compression()
        Ask the server to start compressing the connection.
        Should be called from user of this class after instantiation, as in:
            if 'COMPRESS=DEFLATE' in imapobj.capabilities:
                imapobj.enable_compression()"""

        try:
            typ, dat = self._simple_command('COMPRESS', 'DEFLATE')
            if typ == 'OK':
                self.start_compressing()
                if __debug__: self._log(1, 'Enabled COMPRESS=DEFLATE')
        finally:
            self._release_state_change()


    def pop_untagged_responses(self):
        """ for typ,data in pop_untagged_responses(): pass
        Generator for any remaining untagged responses.
        Returns and removes untagged responses in order of reception.
        Use at your own risk!"""

        while self.untagged_responses:
            self.commands_lock.acquire()
            try:
                yield self.untagged_responses.pop(0)
            finally:
                self.commands_lock.release()


    def recent(self, **kw):
        """(typ, [data]) = recent()
        Return 'RECENT' responses if any exist,
        else prompt server for an update using the 'NOOP' command.
        'data' is None if no new messages,
        else list of RECENT responses, most recent last."""

        name = 'RECENT'
        typ, dat = self._untagged_response(None, [None], name)
        if dat != [None]:
            return self._deliver_dat(typ, dat, kw)
        kw['untagged_response'] = name
        return self.noop(**kw)  # Prod server for response


    def response(self, code, **kw):
        """(code, [data]) = response(code)
        Return data for response 'code' if received, or None.
        Old value for response 'code' is cleared."""

        typ, dat = self._untagged_response(code, [None], code.upper())
        return self._deliver_dat(typ, dat, kw)




    #       IMAP4 commands


    def append(self, mailbox, flags, date_time, message, **kw):
        """(typ, [data]) = append(mailbox, flags, date_time, message)
        Append message to named mailbox.
        All args except `message' can be None."""

        name = 'APPEND'
        if not mailbox:
            mailbox = 'INBOX'
        if flags:
            if (flags[0],flags[-1]) != ('(',')'):
                flags = '(%s)' % flags
        else:
            flags = None
        if date_time:
            date_time = Time2Internaldate(date_time)
        else:
            date_time = None
        self.literal = self.mapCRLF_cre.sub(CRLF, message)
        try:
            return self._simple_command(name, mailbox, flags, date_time, **kw)
        finally:
            self._release_state_change()


    def authenticate(self, mechanism, authobject, **kw):
        """(typ, [data]) = authenticate(mechanism, authobject)
        Authenticate command - requires response processing.

        'mechanism' specifies which authentication mechanism is to
        be used - it must appear in <instance>.capabilities in the
        form AUTH=<mechanism>.

        'authobject' must be a callable object:

                data = authobject(response)

        It will be called to process server continuation responses.
        It should return data that will be encoded and sent to server.
        It should return None if the client abort response '*' should
        be sent instead."""

        self.literal = _Authenticator(authobject).process
        try:
            typ, dat = self._simple_command('AUTHENTICATE', mechanism.upper())
            if typ != 'OK':
                self._deliver_exc(self.error, dat[-1], kw)
            self.state = AUTH
            if __debug__: self._log(1, 'state => AUTH')
        finally:
            self._release_state_change()
        return self._deliver_dat(typ, dat, kw)


    def capability(self, **kw):
        """(typ, [data]) = capability()
        Fetch capabilities list from server."""

        name = 'CAPABILITY'
        kw['untagged_response'] = name
        return self._simple_command(name, **kw)


    def check(self, **kw):
        """(typ, [data]) = check()
        Checkpoint mailbox on server."""

        return self._simple_command('CHECK', **kw)


    def close(self, **kw):
        """(typ, [data]) = close()
        Close currently selected mailbox.

        Deleted messages are removed from writable mailbox.
        This is the recommended command before 'LOGOUT'."""

        if self.state != 'SELECTED':
            raise self.error('No mailbox selected.')
        try:
            typ, dat = self._simple_command('CLOSE')
        finally:
            self.state = AUTH
            if __debug__: self._log(1, 'state => AUTH')
            self._release_state_change()
        return self._deliver_dat(typ, dat, kw)


    def copy(self, message_set, new_mailbox, **kw):
        """(typ, [data]) = copy(message_set, new_mailbox)
        Copy 'message_set' messages onto end of 'new_mailbox'."""

        return self._simple_command('COPY', message_set, new_mailbox, **kw)


    def create(self, mailbox, **kw):
        """(typ, [data]) = create(mailbox)
        Create new mailbox."""

        return self._simple_command('CREATE', mailbox, **kw)


    def delete(self, mailbox, **kw):
        """(typ, [data]) = delete(mailbox)
        Delete old mailbox."""

        return self._simple_command('DELETE', mailbox, **kw)


    def deleteacl(self, mailbox, who, **kw):
        """(typ, [data]) = deleteacl(mailbox, who)
        Delete the ACLs (remove any rights) set for who on mailbox."""

        return self._simple_command('DELETEACL', mailbox, who, **kw)


    def examine(self, mailbox='INBOX', **kw):
        """(typ, [data]) = examine(mailbox='INBOX')
        Select a mailbox for READ-ONLY access. (Flushes all untagged responses.)
        'data' is count of messages in mailbox ('EXISTS' response).
        Mandated responses are ('FLAGS', 'EXISTS', 'RECENT', 'UIDVALIDITY'), so
        other responses should be obtained via "response('FLAGS')" etc."""

        return self.select(mailbox=mailbox, readonly=True, **kw)


    def expunge(self, **kw):
        """(typ, [data]) = expunge()
        Permanently remove deleted items from selected mailbox.
        Generates 'EXPUNGE' response for each deleted message.
        'data' is list of 'EXPUNGE'd message numbers in order received."""

        name = 'EXPUNGE'
        kw['untagged_response'] = name
        return self._simple_command(name, **kw)


    def fetch(self, message_set, message_parts, **kw):
        """(typ, [data, ...]) = fetch(message_set, message_parts)
        Fetch (parts of) messages.
        'message_parts' should be a string of selected parts
        enclosed in parentheses, eg: "(UID BODY[TEXT])".
        'data' are tuples of message part envelope and data,
        followed by a string containing the trailer."""

        name = 'FETCH'
        kw['untagged_response'] = name
        return self._simple_command(name, message_set, message_parts, **kw)


    def getacl(self, mailbox, **kw):
        """(typ, [data]) = getacl(mailbox)
        Get the ACLs for a mailbox."""

        kw['untagged_response'] = 'ACL'
        return self._simple_command('GETACL', mailbox, **kw)


    def getannotation(self, mailbox, entry, attribute, **kw):
        """(typ, [data]) = getannotation(mailbox, entry, attribute)
        Retrieve ANNOTATIONs."""

        kw['untagged_response'] = 'ANNOTATION'
        return self._simple_command('GETANNOTATION', mailbox, entry, attribute, **kw)


    def getquota(self, root, **kw):
        """(typ, [data]) = getquota(root)
        Get the quota root's resource usage and limits.
        (Part of the IMAP4 QUOTA extension defined in rfc2087.)"""

        kw['untagged_response'] = 'QUOTA'
        return self._simple_command('GETQUOTA', root, **kw)


    def getquotaroot(self, mailbox, **kw):
        # Hmmm, this is non-std! Left for backwards-compatibility, sigh.
        # NB: usage should have been defined as:
        #   (typ, [QUOTAROOT responses...]) = getquotaroot(mailbox)
        #   (typ, [QUOTA responses...]) = response('QUOTA')
        """(typ, [[QUOTAROOT responses...], [QUOTA responses...]]) = getquotaroot(mailbox)
        Get the list of quota roots for the named mailbox."""

        typ, dat = self._simple_command('GETQUOTAROOT', mailbox)
        typ, quota = self._untagged_response(typ, dat, 'QUOTA')
        typ, quotaroot = self._untagged_response(typ, dat, 'QUOTAROOT')
        return self._deliver_dat(typ, [quotaroot, quota], kw)


    def id(self, *kv_pairs, **kw):
        """(typ, [data]) = <instance>.id(kv_pairs)
        'kv_pairs' is a possibly empty list of keys and values.
        'data' is a list of ID key value pairs or NIL.
        NB: a single argument is assumed to be correctly formatted and is passed through unchanged
        (for backward compatibility with earlier version).
        Exchange information for problem analysis and determination.
        The ID extension is defined in RFC 2971. """

        name = 'ID'
        kw['untagged_response'] = name

        if not kv_pairs:
            data = 'NIL'
        elif len(kv_pairs) == 1:
            data = kv_pairs[0]     # Assume invoker passing correctly formatted string (back-compat)
        else:
            data = '(%s)' % ' '.join([(arg and self._quote(arg) or 'NIL') for arg in kv_pairs])

        return self._simple_command(name, data, **kw)


    def idle(self, timeout=None, **kw):
        """"(typ, [data]) = idle(timeout=None)
        Put server into IDLE mode until server notifies some change,
        or 'timeout' (secs) occurs (default: 29 minutes),
        or another IMAP4 command is scheduled."""

        name = 'IDLE'
        self.literal = _IdleCont(self, timeout).process
        try:
            return self._simple_command(name, **kw)
        finally:
            self._release_state_change()


    def list(self, directory='""', pattern='*', **kw):
        """(typ, [data]) = list(directory='""', pattern='*')
        List mailbox names in directory matching pattern.
        'data' is list of LIST responses.

        NB: for 'pattern':
        % matches all except separator ( so LIST "" "%" returns names at root)
        * matches all (so LIST "" "*" returns whole directory tree from root)"""

        name = 'LIST'
        kw['untagged_response'] = name
        return self._simple_command(name, directory, pattern, **kw)


    def login(self, user, password, **kw):
        """(typ, [data]) = login(user, password)
        Identify client using plaintext password.
        NB: 'password' will be quoted."""

        try:
            typ, dat = self._simple_command('LOGIN', user, self._quote(password))
            if typ != 'OK':
                self._deliver_exc(self.error, dat[-1], kw)
            self.state = AUTH
            if __debug__: self._log(1, 'state => AUTH')
        finally:
            self._release_state_change()
        return self._deliver_dat(typ, dat, kw)


    def login_cram_md5(self, user, password, **kw):
        """(typ, [data]) = login_cram_md5(user, password)
        Force use of CRAM-MD5 authentication."""

        self.user, self.password = user, password
        return self.authenticate('CRAM-MD5', self._CRAM_MD5_AUTH, **kw)


    def _CRAM_MD5_AUTH(self, challenge):
        """Authobject to use with CRAM-MD5 authentication."""
        import hmac
        pwd = (self.password.encode('ASCII') if isinstance(self.password, str)
                                             else self.password)
        return self.user + " " + hmac.HMAC(pwd, challenge, 'md5').hexdigest()


    def logout(self, **kw):
        """(typ, [data]) = logout()
        Shutdown connection to server.
        Returns server 'BYE' response.
        NB: You must call this to shut down threads before discarding an instance."""

        self.state = LOGOUT
        if __debug__: self._log(1, 'state => LOGOUT')

        try:
            try:
                typ, dat = self._simple_command('LOGOUT')
            except:
                typ, dat = 'NO', ['%s: %s' % sys.exc_info()[:2]]
                if __debug__: self._log(1, dat)

            self._close_threads()
        finally:
            self._release_state_change()

        if __debug__: self._log(1, 'connection closed')

        bye = self._get_untagged_response('BYE', leave=True)
        if bye:
            typ, dat = 'BYE', bye
        return self._deliver_dat(typ, dat, kw)


    def lsub(self, directory='""', pattern='*', **kw):
        """(typ, [data, ...]) = lsub(directory='""', pattern='*')
        List 'subscribed' mailbox names in directory matching pattern.
        'data' are tuples of message part envelope and data."""

        name = 'LSUB'
        kw['untagged_response'] = name
        return self._simple_command(name, directory, pattern, **kw)


    def myrights(self, mailbox, **kw):
        """(typ, [data]) = myrights(mailbox)
        Show my ACLs for a mailbox (i.e. the rights that I have on mailbox)."""

        name = 'MYRIGHTS'
        kw['untagged_response'] = name
        return self._simple_command(name, mailbox, **kw)


    def namespace(self, **kw):
        """(typ, [data, ...]) = namespace()
        Returns IMAP namespaces ala rfc2342."""

        name = 'NAMESPACE'
        kw['untagged_response'] = name
        return self._simple_command(name, **kw)


    def noop(self, **kw):
        """(typ, [data]) = noop()
        Send NOOP command."""

        if __debug__: self._dump_ur(3)
        return self._simple_command('NOOP', **kw)


    def partial(self, message_num, message_part, start, length, **kw):
        """(typ, [data, ...]) = partial(message_num, message_part, start, length)
        Fetch truncated part of a message.
        'data' is tuple of message part envelope and data.
        NB: obsolete."""

        name = 'PARTIAL'
        kw['untagged_response'] = 'FETCH'
        return self._simple_command(name, message_num, message_part, start, length, **kw)


    def proxyauth(self, user, **kw):
        """(typ, [data]) = proxyauth(user)
        Assume authentication as 'user'.
        (Allows an authorised administrator to proxy into any user's mailbox.)"""

        try:
            return self._simple_command('PROXYAUTH', user, **kw)
        finally:
            self._release_state_change()


    def rename(self, oldmailbox, newmailbox, **kw):
        """(typ, [data]) = rename(oldmailbox, newmailbox)
        Rename old mailbox name to new."""

        return self._simple_command('RENAME', oldmailbox, newmailbox, **kw)


    def search(self, charset, *criteria, **kw):
        """(typ, [data]) = search(charset, criterion, ...)
        Search mailbox for matching messages.
        'data' is space separated list of matching message numbers."""

        name = 'SEARCH'
        kw['untagged_response'] = name
        if charset:
            return self._simple_command(name, 'CHARSET', charset, *criteria, **kw)
        return self._simple_command(name, *criteria, **kw)


    def select(self, mailbox='INBOX', readonly=False, **kw):
        """(typ, [data]) = select(mailbox='INBOX', readonly=False)
        Select a mailbox. (Flushes all untagged responses.)
        'data' is count of messages in mailbox ('EXISTS' response).
        Mandated responses are ('FLAGS', 'EXISTS', 'RECENT', 'UIDVALIDITY'), so
        other responses should be obtained via "response('FLAGS')" etc."""

        self.mailbox = mailbox

        self.is_readonly = bool(readonly)
        if readonly:
            name = 'EXAMINE'
        else:
            name = 'SELECT'
        try:
            rqb = self._command(name, mailbox)
            typ, dat = rqb.get_response('command: %s => %%s' % rqb.name)
            if typ != 'OK':
                if self.state == SELECTED:
                    self.state = AUTH
                if __debug__: self._log(1, 'state => AUTH')
                if typ == 'BAD':
                    self._deliver_exc(self.error, '%s command error: %s %s. Data: %.100s' % (name, typ, dat, mailbox), kw)
                return self._deliver_dat(typ, dat, kw)
            self.state = SELECTED
            if __debug__: self._log(1, 'state => SELECTED')
        finally:
            self._release_state_change()

        if self._get_untagged_response('READ-ONLY', leave=True) and not readonly:
            if __debug__: self._dump_ur(1)
            self._deliver_exc(self.readonly, '%s is not writable' % mailbox, kw)
        typ, dat = self._untagged_response(typ, [None], 'EXISTS')
        return self._deliver_dat(typ, dat, kw)


    def setacl(self, mailbox, who, what, **kw):
        """(typ, [data]) = setacl(mailbox, who, what)
        Set a mailbox acl."""

        try:
            return self._simple_command('SETACL', mailbox, who, what, **kw)
        finally:
            self._release_state_change()


    def setannotation(self, *args, **kw):
        """(typ, [data]) = setannotation(mailbox[, entry, attribute]+)
        Set ANNOTATIONs."""

        kw['untagged_response'] = 'ANNOTATION'
        return self._simple_command('SETANNOTATION', *args, **kw)


    def setquota(self, root, limits, **kw):
        """(typ, [data]) = setquota(root, limits)
        Set the quota root's resource limits."""

        kw['untagged_response'] = 'QUOTA'
        try:
            return self._simple_command('SETQUOTA', root, limits, **kw)
        finally:
            self._release_state_change()


    def sort(self, sort_criteria, charset, *search_criteria, **kw):
        """(typ, [data]) = sort(sort_criteria, charset, search_criteria, ...)
        IMAP4rev1 extension SORT command."""

        name = 'SORT'
        if (sort_criteria[0],sort_criteria[-1]) != ('(',')'):
            sort_criteria = '(%s)' % sort_criteria
        kw['untagged_response'] = name
        return self._simple_command(name, sort_criteria, charset, *search_criteria, **kw)


    def starttls(self, keyfile=None, certfile=None, ca_certs=None, cert_verify_cb=None, ssl_version="ssl23", tls_level=TLS_COMPAT, **kw):
        """(typ, [data]) = starttls(keyfile=None, certfile=None, ca_certs=None, cert_verify_cb=None, ssl_version="ssl23", tls_level="tls_compat")
        Start TLS negotiation as per RFC 2595."""

        name = 'STARTTLS'

        if name not in self.capabilities:
            raise self.abort('TLS not supported by server')

        if self._tls_established:
            raise self.abort('TLS session already established')

        # Must now shutdown reader thread after next response, and restart after changing read_fd

        self.read_size = 1                # Don't consume TLS handshake
        self.TerminateReader = True

        try:
            typ, dat = self._simple_command(name)
        finally:
            self._release_state_change()
            self.rdth.join()
            self.TerminateReader = False
            self.read_size = READ_SIZE

        if typ != 'OK':
            # Restart reader thread and error
            self.rdth = threading.Thread(target=self._reader)
            self.rdth.setDaemon(True)
            self.rdth.start()
            raise self.error("Couldn't establish TLS session: %s" % dat)

        self.keyfile = keyfile
        self.certfile = certfile
        self.ca_certs = ca_certs
        self.cert_verify_cb = cert_verify_cb
        self.ssl_version = ssl_version
        self.tls_level = tls_level

        try:
            self.ssl_wrap_socket()
        finally:
            # Restart reader thread
            self.rdth = threading.Thread(target=self._reader)
            self.rdth.setDaemon(True)
            self.rdth.start()

        typ, dat = self.capability()
        if dat == [None]:
            raise self.error('no CAPABILITY response from server')
        self.capabilities = tuple(dat[-1].upper().split())

        self._tls_established = True

        typ, dat = self._untagged_response(typ, dat, name)
        return self._deliver_dat(typ, dat, kw)


    def status(self, mailbox, names, **kw):
        """(typ, [data]) = status(mailbox, names)
        Request named status conditions for mailbox."""

        name = 'STATUS'
        kw['untagged_response'] = name
        return self._simple_command(name, mailbox, names, **kw)


    def store(self, message_set, command, flags, **kw):
        """(typ, [data]) = store(message_set, command, flags)
        Alters flag dispositions for messages in mailbox."""

        if (flags[0],flags[-1]) != ('(',')'):
            flags = '(%s)' % flags  # Avoid quoting the flags
        kw['untagged_response'] = 'FETCH'
        return self._simple_command('STORE', message_set, command, flags, **kw)


    def subscribe(self, mailbox, **kw):
        """(typ, [data]) = subscribe(mailbox)
        Subscribe to new mailbox."""

        try:
            return self._simple_command('SUBSCRIBE', mailbox, **kw)
        finally:
            self._release_state_change()


    def thread(self, threading_algorithm, charset, *search_criteria, **kw):
        """(type, [data]) = thread(threading_alogrithm, charset, search_criteria, ...)
        IMAPrev1 extension THREAD command."""

        name = 'THREAD'
        kw['untagged_response'] = name
        return self._simple_command(name, threading_algorithm, charset, *search_criteria, **kw)


    def uid(self, command, *args, **kw):
        """(typ, [data]) = uid(command, arg, ...)
        Execute "command arg ..." with messages identified by UID,
            rather than message number.
        Assumes 'command' is legal in current state.
        Returns response appropriate to 'command'."""

        command = command.upper()
        if command in UID_direct:
            resp = command
        else:
            resp = 'FETCH'
        kw['untagged_response'] = resp
        return self._simple_command('UID', command, *args, **kw)


    def unsubscribe(self, mailbox, **kw):
        """(typ, [data]) = unsubscribe(mailbox)
        Unsubscribe from old mailbox."""

        try:
            return self._simple_command('UNSUBSCRIBE', mailbox, **kw)
        finally:
            self._release_state_change()


    def xatom(self, name, *args, **kw):
        """(typ, [data]) = xatom(name, arg, ...)
        Allow simple extension commands notified by server in CAPABILITY response.
        Assumes extension command 'name' is legal in current state.
        Returns response appropriate to extension command 'name'."""

        name = name.upper()
        if not name in Commands:
            Commands[name] = ((self.state,), False)
        try:
            return self._simple_command(name, *args, **kw)
        finally:
            self._release_state_change()



    #       Internal methods


    def _append_untagged(self, typ, dat):

        # Append new 'dat' to end of last untagged response if same 'typ',
        # else append new response.

        if dat is None: dat = ''

        self.commands_lock.acquire()

        if self.untagged_responses:
            urn, urd = self.untagged_responses[-1]
            if urn != typ:
                 urd = None
        else:
            urd = None

        if urd is None:
            urd = []
            self.untagged_responses.append([typ, urd])

        urd.append(dat)

        self.commands_lock.release()

        if __debug__: self._log(5, 'untagged_responses[%s] %s += ["%.80s"]' % (typ, len(urd)-1, dat))


    def _check_bye(self):

        bye = self._get_untagged_response('BYE', leave=True)
        if bye:
            if str != bytes:
                raise self.abort(bye[-1].decode('ASCII', 'replace'))
            else:
                raise self.abort(bye[-1])


    def _checkquote(self, arg):

        # Must quote command args if "atom-specials" present,
        # and not already quoted. NB: single quotes are removed.

        if not isinstance(arg, string_types):
            return arg
        if len(arg) >= 2 and (arg[0],arg[-1]) in (('(',')'),('"','"')):
            return arg
        if len(arg) >= 2 and (arg[0],arg[-1]) in (("'","'"),):
            return arg[1:-1]
        if arg and self.mustquote_cre.search(arg) is None:
            return arg
        return self._quote(arg)


    def _choose_nonull_or_dflt(self, dflt, *args):
        if isinstance(dflt, string_types):
            dflttyp = string_types            # Allow any string type
        else:
            dflttyp = type(dflt)
        for arg in args:
            if arg is not None:
                 if isinstance(arg, dflttyp):
                     return arg
                 if __debug__: self._log(0, 'bad arg is %s, expecting %s' % (type(arg), dflttyp))
        return dflt


    def _command(self, name, *args, **kw):

        if Commands[name][CMD_VAL_ASYNC]:
            cmdtyp = 'async'
        else:
            cmdtyp = 'sync'

        if __debug__: self._log(1, '[%s] %s %s' % (cmdtyp, name, args))

        if __debug__: self._log(3, 'state_change_pending.acquire')
        self.state_change_pending.acquire()

        self._end_idle()

        if cmdtyp == 'async':
            self.state_change_pending.release()
            if __debug__: self._log(3, 'state_change_pending.release')
        else:
            # Need to wait for all async commands to complete
            self._check_bye()
            self.commands_lock.acquire()
            if self.tagged_commands:
                self.state_change_free.clear()
                need_event = True
            else:
                need_event = False
            self.commands_lock.release()
            if need_event:
                if __debug__: self._log(3, 'sync command %s waiting for empty commands Q' % name)
                self.state_change_free.wait(threading.TIMEOUT_MAX)
                if __debug__: self._log(3, 'sync command %s proceeding' % name)

        if self.state not in Commands[name][CMD_VAL_STATES]:
            self.literal = None
            raise self.error('command %s illegal in state %s, only allowed in states %s'
                                % (name, self.state, ', '.join(Commands[name][CMD_VAL_STATES])))

        self._check_bye()

        if name in ('EXAMINE', 'SELECT'):
            self.commands_lock.acquire()
            self.untagged_responses = []      # Flush all untagged responses
            self.commands_lock.release()
        else:
            for typ in ('OK', 'NO', 'BAD'):
                while self._get_untagged_response(typ):
                    continue

            if not self.is_readonly and self._get_untagged_response('READ-ONLY', leave=True):
                self.literal = None
                raise self.readonly('mailbox status changed to READ-ONLY')

        if self.Terminate:
            raise self.abort('connection closed')

        rqb = self._request_push(name=name, **kw)

        data = '%s %s' % (rqb.tag, name)
        for arg in args:
            if arg is None: continue
            data = '%s %s' % (data, self._checkquote(arg))

        literal = self.literal
        if literal is not None:
            self.literal = None
            if isinstance(literal, string_types):
                literator = None
                data = '%s {%s}' % (data, len(literal))
            else:
                literator = literal

        if __debug__: self._log(4, 'data=%s' % data)

        rqb.data = '%s%s' % (data, CRLF)

        if literal is None:
            self.ouq.put(rqb)
            return rqb

        # Must setup continuation expectancy *before* ouq.put 
        crqb = self._request_push(name=name, tag='continuation')

        self.ouq.put(rqb)

        while True:
            # Wait for continuation response

            ok, data = crqb.get_response('command: %s => %%s' % name)
            if __debug__: self._log(4, 'continuation => %s, %s' % (ok, data))

            # NO/BAD response?

            if not ok:
                break

            # Send literal

            if literator is not None:
                literal = literator(data, rqb)

            if literal is None:
                break

            if literator is not None:
                # Need new request for next continuation response
                crqb = self._request_push(name=name, tag='continuation')

            if __debug__: self._log(4, 'write literal size %s' % len(literal))
            crqb.data = '%s%s' % (literal, CRLF)
            self.ouq.put(crqb)

            if literator is None:
                break

        return rqb


    def _command_complete(self, rqb, kw):

        # Called for non-callback commands

        self._check_bye()
        typ, dat = rqb.get_response('command: %s => %%s' % rqb.name)
        if typ == 'BAD':
            if __debug__: self._print_log()
            raise self.error('%s command error: %s %s. Data: %.100s' % (rqb.name, typ, dat, rqb.data))
        if 'untagged_response' in kw:
            return self._untagged_response(typ, dat, kw['untagged_response'])
        return typ, dat


    def _command_completer(self, cb_arg_list):

        # Called for callback commands
        response, cb_arg, error = cb_arg_list
        rqb, kw = cb_arg
        rqb.callback = kw['callback']
        rqb.callback_arg = kw.get('cb_arg')
        if error is not None:
            if __debug__: self._print_log()
            typ, val = error
            rqb.abort(typ, val)
            return
        bye = self._get_untagged_response('BYE', leave=True)
        if bye:
            if str != bytes:
               rqb.abort(self.abort, bye[-1].decode('ASCII', 'replace'))
            else:
               rqb.abort(self.abort, bye[-1])
            return
        typ, dat = response
        if typ == 'BAD':
            if __debug__: self._print_log()
            rqb.abort(self.error, '%s command error: %s %s. Data: %.100s' % (rqb.name, typ, dat, rqb.data))
            return
        if __debug__: self._log(4, '_command_completer(%s, %s, None) = %s' % (response, cb_arg, rqb.tag))
        if 'untagged_response' in kw:
            response = self._untagged_response(typ, dat, kw['untagged_response'])
        rqb.deliver(response)


    def _deliver_dat(self, typ, dat, kw):

        if 'callback' in kw:
            kw['callback'](((typ, dat), kw.get('cb_arg'), None))
        return typ, dat


    def _deliver_exc(self, exc, dat, kw):

        if 'callback' in kw:
            kw['callback']((None, kw.get('cb_arg'), (exc, dat)))
        raise exc(dat)


    def _end_idle(self):

        self.idle_lock.acquire()
        irqb = self.idle_rqb
        if irqb is None:
            self.idle_lock.release()
            return
        self.idle_rqb = None
        self.idle_timeout = None
        self.idle_lock.release()
        irqb.data = 'DONE%s' % CRLF
        self.ouq.put(irqb)
        if __debug__: self._log(2, 'server IDLE finished')


    def _get_untagged_response(self, name, leave=False):

        self.commands_lock.acquire()

        for i, (typ, dat) in enumerate(self.untagged_responses):
            if typ == name:
                if not leave:
                    del self.untagged_responses[i]
                self.commands_lock.release()
                if __debug__: self._log(5, '_get_untagged_response(%s) => %.80s' % (name, dat))
                return dat

        self.commands_lock.release()
        return None


    def _match(self, cre, s):

        # Run compiled regular expression 'cre' match method on 's'.
        # Save result, return success.

        self.mo = cre.match(s)
        return self.mo is not None


    def _put_response(self, resp):

        if self._expecting_data:
            rlen = len(resp)
            dlen = min(self._expecting_data_len, rlen)
            if __debug__: self._log(5, '_put_response expecting data len %s, got %s' % (self._expecting_data_len, rlen))
            self._expecting_data_len -= dlen
            self._expecting_data = (self._expecting_data_len != 0)
            if rlen <= dlen:
                self._accumulated_data.append(resp)
                return
            self._accumulated_data.append(resp[:dlen])
            resp = resp[dlen:]

        if self._accumulated_data:
            typ, dat = self._literal_expected
            self._append_untagged(typ, (dat, ''.join(self._accumulated_data)))
            self._accumulated_data = []

        # Protocol mandates all lines terminated by CRLF
        resp = resp[:-2]
        if __debug__: self._log(5, '_put_response(%s)' % resp)

        if 'continuation' in self.tagged_commands:
            continuation_expected = True
        else:
            continuation_expected = False

        if self._literal_expected is not None:
            dat = resp
            if self._match(self.literal_cre, dat):
                self._literal_expected[1] = dat
                self._expecting_data = True
                self._expecting_data_len = int(self.mo.group('size'))
                if __debug__: self._log(4, 'expecting literal size %s' % self._expecting_data_len)
                return
            typ = self._literal_expected[0]
            self._literal_expected = None
            if dat:
                self._append_untagged(typ, dat)  # Tail
            if __debug__: self._log(4, 'literal completed')
        else:
            # Command completion response?
            if self._match(self.tagre, resp):
                tag = self.mo.group('tag')
                typ = self.mo.group('type')
                dat = self.mo.group('data')
                if typ in ('OK', 'NO', 'BAD') and self._match(self.response_code_cre, dat):
                    self._append_untagged(self.mo.group('type'), self.mo.group('data'))
                if not tag in self.tagged_commands:
                    if __debug__: self._log(1, 'unexpected tagged response: %s' % resp)
                else:
                    self._request_pop(tag, (typ, [dat]))
            else:
                dat2 = None

                # '*' (untagged) responses?

                if not self._match(self.untagged_response_cre, resp):
                    if self._match(self.untagged_status_cre, resp):
                        dat2 = self.mo.group('data2')

                if self.mo is None:
                    # Only other possibility is '+' (continuation) response...

                    if self._match(self.continuation_cre, resp):
                        if not continuation_expected:
                            if __debug__: self._log(1, "unexpected continuation response: '%s'" % resp)
                            return
                        self._request_pop('continuation', (True, self.mo.group('data')))
                        return

                    if __debug__: self._log(1, "unexpected response: '%s'" % resp)
                    return

                typ = self.mo.group('type')
                dat = self.mo.group('data')
                if dat is None: dat = ''        # Null untagged response
                if dat2: dat = dat + ' ' + dat2

                # Is there a literal to come?

                if self._match(self.literal_cre, dat):
                    self._expecting_data = True
                    self._expecting_data_len = int(self.mo.group('size'))
                    if __debug__: self._log(4, 'read literal size %s' % self._expecting_data_len)
                    self._literal_expected = [typ, dat]
                    return

                self._append_untagged(typ, dat)
                if typ in ('OK', 'NO', 'BAD') and self._match(self.response_code_cre, dat):
                    self._append_untagged(self.mo.group('type'), self.mo.group('data'))

                if typ != 'OK':                 # NO, BYE, IDLE
                    self._end_idle()

        # Command waiting for aborted continuation response?

        if continuation_expected:
            self._request_pop('continuation', (False, resp))

        # Bad news?

        if typ in ('NO', 'BAD', 'BYE'):
            if typ == 'BYE':
                self.Terminate = True
            if __debug__: self._log(1, '%s response: %s' % (typ, dat))


    def _quote(self, arg):

        return '"%s"' % arg.replace('\\', '\\\\').replace('"', '\\"')


    def _release_state_change(self):

        if self.state_change_pending.locked():
            self.state_change_pending.release()
            if __debug__: self._log(3, 'state_change_pending.release')


    def _request_pop(self, name, data):

        self.commands_lock.acquire()
        rqb = self.tagged_commands.pop(name)
        if not self.tagged_commands:
            need_event = True
        else:
            need_event = False
        self.commands_lock.release()

        if __debug__: self._log(4, '_request_pop(%s, %s) [%d] = %s' % (name, data, len(self.tagged_commands), rqb.tag))
        rqb.deliver(data)

        if need_event:
            if __debug__: self._log(3, 'state_change_free.set')
            self.state_change_free.set()


    def _request_push(self, tag=None, name=None, **kw):

        self.commands_lock.acquire()
        rqb = Request(self, name=name, **kw)
        if tag is None:
            tag = rqb.tag
        self.tagged_commands[tag] = rqb
        self.commands_lock.release()
        if __debug__: self._log(4, '_request_push(%s, %s, %s) = %s' % (tag, name, repr(kw), rqb.tag))
        return rqb


    def _simple_command(self, name, *args, **kw):

        if 'callback' in kw:
            # Note: old calling sequence for back-compat with python <2.6
            self._command(name, callback=self._command_completer, cb_arg=kw, cb_self=True, *args)
            return (None, None)
        return self._command_complete(self._command(name, *args), kw)


    def _untagged_response(self, typ, dat, name):

        if typ == 'NO':
            return typ, dat
        data = self._get_untagged_response(name)
        if not data:
            return typ, [None]
        while True:
            dat = self._get_untagged_response(name)
            if not dat:
                break
            data += dat
        if __debug__: self._log(4, '_untagged_response(%s, ?, %s) => %.80s' % (typ, name, data))
        return typ, data



    #       Threads


    def _close_threads(self):

        if __debug__: self._log(1, '_close_threads')

        self.ouq.put(None)
        self.wrth.join()

        if __debug__: self._log(1, 'call shutdown')

        self.shutdown()

        self.rdth.join()
        self.inth.join()


    def _handler(self):

        resp_timeout = self.resp_timeout

        threading.currentThread().setName(self.identifier + 'handler')

        time.sleep(0.1)   # Don't start handling before main thread ready

        if __debug__: self._log(1, 'starting')

        typ, val = self.abort, 'connection terminated'

        while not self.Terminate:

            self.idle_lock.acquire()
            if self.idle_timeout is not None:
                timeout = self.idle_timeout - time.time()
                if timeout <= 0:
                    timeout = 1
                if __debug__:
                    if self.idle_rqb is not None:
                        self._log(5, 'server IDLING, timeout=%.2f' % timeout)
            else:
                timeout = resp_timeout
            self.idle_lock.release()

            try:
                line = self.inq.get(True, timeout)
            except queue.Empty:
                if self.idle_rqb is None:
                    if resp_timeout is not None and self.tagged_commands:
                        if __debug__: self._log(1, 'response timeout')
                        typ, val = self.abort, 'no response after %s secs' % resp_timeout
                        break
                    continue
                if self.idle_timeout > time.time():
                    continue
                if __debug__: self._log(2, 'server IDLE timedout')
                line = IDLE_TIMEOUT_RESPONSE

            if line is None:
                if __debug__: self._log(1, 'inq None - terminating')
                break

            if not isinstance(line, string_types):
                typ, val = line
                break

            try:
                self._put_response(line)
            except:
                typ, val = self.error, 'program error: %s - %s' % sys.exc_info()[:2]
                break

        self.Terminate = True

        if __debug__: self._log(1, 'terminating: %s' % repr(val))

        while not self.ouq.empty():
            try:
                qel = self.ouq.get_nowait()
                if qel is not None:
                    qel.abort(typ, val)
            except queue.Empty:
                break
        self.ouq.put(None)

        self.commands_lock.acquire()
        for name in list(self.tagged_commands.keys()):
            rqb = self.tagged_commands.pop(name)
            rqb.abort(typ, val)
        self.state_change_free.set()
        self.commands_lock.release()
        if __debug__: self._log(3, 'state_change_free.set')

        if __debug__: self._log(1, 'finished')


    if hasattr(select_module, "poll"):

      def _reader(self):

        threading.currentThread().setName(self.identifier + 'reader')

        if __debug__: self._log(1, 'starting using poll')

        def poll_error(state):
            PollErrors = {
                select.POLLERR:     'Error',
                select.POLLHUP:     'Hang up',
                select.POLLNVAL:    'Invalid request: descriptor not open',
            }
            return ' '.join([PollErrors[s] for s in PollErrors.keys() if (s & state)])

        if bytes != str:
            line_part = b''
        else:
            line_part = ''

        poll = select.poll()

        poll.register(self.read_fd, select.POLLIN)

        rxzero = 0
        terminate = False
        read_poll_timeout = self.read_poll_timeout * 1000       # poll() timeout is in millisecs

        while not (terminate or self.Terminate):
            if self.state == LOGOUT:
                timeout = 10
            else:
                timeout = read_poll_timeout
            try:
                r = poll.poll(timeout)
                if __debug__: self._log(5, 'poll => %s' % repr(r))
                if not r:
                    continue                                    # Timeout

                fd,state = r[0]

                if state & select.POLLIN:
                    data = self.read(self.read_size)            # Drain ssl buffer if present
                    start = 0
                    dlen = len(data)
                    if __debug__: self._log(5, 'rcvd %s' % dlen)
                    if dlen == 0:
                        rxzero += 1
                        if rxzero > 5:
                            raise IOError("Too many read 0")
                        time.sleep(0.1)
                        continue                                # Try again
                    rxzero = 0

                    while True:
                        if bytes != str:
                            stop = data.find(b'\n', start)
                            if stop < 0:
                                line_part += data[start:]
                                break
                            stop += 1
                            line_part, start, line = \
                                b'', stop, (line_part + data[start:stop]).decode(errors='ignore')
                        else:
                            stop = data.find('\n', start)
                            if stop < 0:
                                line_part += data[start:]
                                break
                            stop += 1
                            line_part, start, line = \
                                '', stop, line_part + data[start:stop]
                        if __debug__: self._log(4, '< %s' % line)
                        self.inq.put(line)
                        if self.TerminateReader:
                            terminate = True

                if state & ~(select.POLLIN):
                    raise IOError(poll_error(state))
            except:
                reason = 'socket error: %s - %s' % sys.exc_info()[:2]
                if __debug__:
                    if not self.Terminate:
                        self._print_log()
                        if self.debug: self.debug += 4          # Output all
                        self._log(1, reason)
                self.inq.put((self.abort, reason))
                break

        poll.unregister(self.read_fd)

        if __debug__: self._log(1, 'finished')

    else:

      # No "poll" - use select()

      def _reader(self):

        threading.currentThread().setName(self.identifier + 'reader')

        if __debug__: self._log(1, 'starting using select')

        if bytes != str:
            line_part = b''
        else:
            line_part = ''

        rxzero = 0
        terminate = False

        while not (terminate or self.Terminate):
            if self.state == LOGOUT:
                timeout = 1
            else:
                timeout = self.read_poll_timeout
            try:
                r,w,e = select.select([self.read_fd], [], [], timeout)
                if __debug__: self._log(5, 'select => %s, %s, %s' % (r,w,e))
                if not r:                                       # Timeout
                    continue

                data = self.read(self.read_size)                # Drain ssl buffer if present
                start = 0
                dlen = len(data)
                if __debug__: self._log(5, 'rcvd %s' % dlen)
                if dlen == 0:
                    rxzero += 1
                    if rxzero > 5:
                        raise IOError("Too many read 0")
                    time.sleep(0.1)
                    continue                                    # Try again
                rxzero = 0

                while True:
                    if bytes != str:
                        stop = data.find(b'\n', start)
                        if stop < 0:
                            line_part += data[start:]
                            break
                        stop += 1
                        line_part, start, line = \
                            b'', stop, (line_part + data[start:stop]).decode(errors='ignore')
                    else:
                        stop = data.find('\n', start)
                        if stop < 0:
                            line_part += data[start:]
                            break
                        stop += 1
                        line_part, start, line = \
                            '', stop, line_part + data[start:stop]
                    if __debug__: self._log(4, '< %s' % line)
                    self.inq.put(line)
                    if self.TerminateReader:
                        terminate = True
            except:
                reason = 'socket error: %s - %s' % sys.exc_info()[:2]
                if __debug__:
                    if not self.Terminate:
                        self._print_log()
                        if self.debug: self.debug += 4          # Output all
                        self._log(1, reason)
                self.inq.put((self.abort, reason))
                break

        if __debug__: self._log(1, 'finished')


    def _writer(self):

        threading.currentThread().setName(self.identifier + 'writer')

        if __debug__: self._log(1, 'starting')

        reason = 'Terminated'

        while not self.Terminate:
            rqb = self.ouq.get()
            if rqb is None:
                break   # Outq flushed

            try:
                self.send(rqb.data)
                if __debug__: self._log(4, '> %s' % rqb.data)
            except:
                reason = 'socket error: %s - %s' % sys.exc_info()[:2]
                if __debug__:
                    if not self.Terminate:
                        self._print_log()
                        if self.debug: self.debug += 4          # Output all
                        self._log(1, reason)
                rqb.abort(self.abort, reason)
                break

        self.inq.put((self.abort, reason))

        if __debug__: self._log(1, 'finished')



    #       Debugging


    if __debug__:

        def _init_debug(self, debug=None, debug_file=None, debug_buf_lvl=None):
            self.debug_lock = threading.Lock()

            self.debug = self._choose_nonull_or_dflt(0, debug, Debug)
            self.debug_file = self._choose_nonull_or_dflt(sys.stderr, debug_file)
            self.debug_buf_lvl = self._choose_nonull_or_dflt(DFLT_DEBUG_BUF_LVL, debug_buf_lvl)

            self._cmd_log_len = 20
            self._cmd_log_idx = 0
            self._cmd_log = {}           # Last `_cmd_log_len' interactions
            if self.debug:
                self._mesg('imaplib2 version %s' % __version__)
                self._mesg('imaplib2 debug level %s, buffer level %s' % (self.debug, self.debug_buf_lvl))


        def _dump_ur(self, lvl):
            if lvl > self.debug:
                return

            l = self.untagged_responses
            if not l:
                return

            t = '\n\t\t'
            l = ['%s: "%s"' % (x[0], x[1][0] and '" "'.join(x[1]) or '') for x in l]
            self.debug_lock.acquire()
            self._mesg('untagged responses dump:%s%s' % (t, t.join(l)))
            self.debug_lock.release()


        def _log(self, lvl, line):
            if lvl > self.debug:
                return

            if line[-2:] == CRLF:
                line = line[:-2] + '\\r\\n'

            tn = threading.currentThread().getName()

            if lvl <= 1 or self.debug > self.debug_buf_lvl:
                self.debug_lock.acquire()
                self._mesg(line, tn)
                self.debug_lock.release()
                if lvl != 1:
                    return

            # Keep log of last `_cmd_log_len' interactions for debugging.
            self.debug_lock.acquire()
            self._cmd_log[self._cmd_log_idx] = (line, tn, time.time())
            self._cmd_log_idx += 1
            if self._cmd_log_idx >= self._cmd_log_len:
                self._cmd_log_idx = 0
            self.debug_lock.release()


        def _mesg(self, s, tn=None, secs=None):
            if secs is None:
                secs = time.time()
            if tn is None:
                tn = threading.currentThread().getName()
            tm = time.strftime('%M:%S', time.localtime(secs))
            try:
                self.debug_file.write('  %s.%02d %s %s\n' % (tm, (secs*100)%100, tn, s))
                self.debug_file.flush()
            finally:
                pass


        def _print_log(self):
            self.debug_lock.acquire()
            i, n = self._cmd_log_idx, self._cmd_log_len
            if n: self._mesg('last %d log messages:' % n)
            while n:
                try:
                    self._mesg(*self._cmd_log[i])
                except:
                    pass
                i += 1
                if i >= self._cmd_log_len:
                    i = 0
                n -= 1
            self.debug_lock.release()



class IMAP4_SSL(IMAP4):

    """IMAP4 client class over SSL connection

    Instantiate with:
        IMAP4_SSL(host=None, port=None, keyfile=None, certfile=None, ca_certs=None, cert_verify_cb=None, ssl_version="ssl23", debug=None, debug_file=None, identifier=None, timeout=None, debug_buf_lvl=None, tls_level="tls_compat")

        host           - host's name (default: localhost);
        port           - port number (default: standard IMAP4 SSL port);
        keyfile        - PEM formatted file that contains your private key (default: None);
        certfile       - PEM formatted certificate chain file (default: None);
        ca_certs       - PEM formatted certificate chain file used to validate server certificates (default: None);
        cert_verify_cb - function to verify authenticity of server certificates (default: None);
        ssl_version    - SSL version to use (default: "ssl23", choose from: "tls1","ssl3","ssl23");
        debug          - debug level (default: 0 - no debug);
        debug_file     - debug stream (default: sys.stderr);
        identifier     - thread identifier prefix (default: host);
        timeout        - timeout in seconds when expecting a command response.
        debug_buf_lvl  - debug level at which buffering is turned off.
        tls_level      - TLS security level (default: "tls_compat").

    The recognized values for tls_level are:
        tls_secure: accept only TLS protocols recognized as "secure"
        tls_no_ssl: disable SSLv2 and SSLv3 support
        tls_compat: accept all SSL/TLS versions

    For more documentation see the docstring of the parent class IMAP4.
    """


    def __init__(self, host=None, port=None, keyfile=None, certfile=None, ca_certs=None, cert_verify_cb=None, ssl_version="ssl23", debug=None, debug_file=None, identifier=None, timeout=None, debug_buf_lvl=None, tls_level=TLS_COMPAT):
        self.keyfile = keyfile
        self.certfile = certfile
        self.ca_certs = ca_certs
        self.cert_verify_cb = cert_verify_cb
        self.ssl_version = ssl_version
        self.tls_level = tls_level
        IMAP4.__init__(self, host, port, debug, debug_file, identifier, timeout, debug_buf_lvl)


    def open(self, host=None, port=None):
        """open(host=None, port=None)
        Setup secure connection to remote server on "host:port"
            (default: localhost:standard IMAP4 SSL port).
        This connection will be used by the routines:
            read, send, shutdown, socket, ssl."""

        self.host = self._choose_nonull_or_dflt('', host)
        self.port = self._choose_nonull_or_dflt(IMAP4_SSL_PORT, port)
        self.sock = self.open_socket()
        self.ssl_wrap_socket()


    def read(self, size):
        """data = read(size)
        Read at most 'size' bytes from remote."""

        if self.decompressor is None:
            return self.sock.read(size)

        if self.decompressor.unconsumed_tail:
            data = self.decompressor.unconsumed_tail
        else:
            data = self.sock.read(READ_SIZE)

        return self.decompressor.decompress(data, size)


    def send(self, data):
        """send(data)
        Send 'data' to remote."""

        if self.compressor is not None:
            data = self.compressor.compress(data)
            data += self.compressor.flush(zlib.Z_SYNC_FLUSH)

        if bytes != str:
            data = bytes(data, 'utf8')

        if hasattr(self.sock, "sendall"):
            self.sock.sendall(data)
        else:
            dlen = len(data)
            while dlen > 0:
                sent = self.sock.write(data)
                if sent == dlen:
                    break    # avoid copy
                data = data[sent:]
                dlen = dlen - sent


    def ssl(self):
        """ssl = ssl()
        Return ssl instance used to communicate with the IMAP4 server."""

        return self.sock



class IMAP4_stream(IMAP4):

    """IMAP4 client class over a stream

    Instantiate with:
        IMAP4_stream(command, debug=None, debug_file=None, identifier=None, timeout=None, debug_buf_lvl=None)

        command        - string that can be passed to subprocess.Popen();
        debug          - debug level (default: 0 - no debug);
        debug_file     - debug stream (default: sys.stderr);
        identifier     - thread identifier prefix (default: host);
        timeout        - timeout in seconds when expecting a command response.
        debug_buf_lvl  - debug level at which buffering is turned off.

    For more documentation see the docstring of the parent class IMAP4.
    """


    def __init__(self, command, debug=None, debug_file=None, identifier=None, timeout=None, debug_buf_lvl=None):
        self.command = command
        self.host = command
        self.port = None
        self.sock = None
        self.writefile, self.readfile = None, None
        self.read_fd = None
        IMAP4.__init__(self, None, None, debug, debug_file, identifier, timeout, debug_buf_lvl)


    def open(self, host=None, port=None):
        """open(host=None, port=None)
        Setup a stream connection via 'self.command'.
        This connection will be used by the routines:
            read, send, shutdown, socket."""

        from subprocess import Popen, PIPE

        if __debug__: self._log(0, 'opening stream from command "%s"' % self.command)
        self._P = Popen(self.command, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
        self.writefile, self.readfile = self._P.stdin, self._P.stdout
        self.read_fd = self.readfile.fileno()


    def read(self, size):
        """Read 'size' bytes from remote."""

        if self.decompressor is None:
            return os.read(self.read_fd, size)

        if self.decompressor.unconsumed_tail:
            data = self.decompressor.unconsumed_tail
        else:
            data = os.read(self.read_fd, READ_SIZE)

        return self.decompressor.decompress(data, size)


    def send(self, data):
        """Send data to remote."""

        if self.compressor is not None:
            data = self.compressor.compress(data)
            data += self.compressor.flush(zlib.Z_SYNC_FLUSH)

        if bytes != str:
            data = bytes(data, 'utf8')

        self.writefile.write(data)
        self.writefile.flush()


    def shutdown(self):
        """Close I/O established in "open"."""

        self.readfile.close()
        self.writefile.close()


class _Authenticator(object):

    """Private class to provide en/de-coding
    for base64 authentication conversation."""

    def __init__(self, mechinst):
        self.mech = mechinst    # Callable object to provide/process data

    def process(self, data, rqb):
        ret = self.mech(self.decode(data))
        if ret is None:
            return '*'      # Abort conversation
        return self.encode(ret)

    def encode(self, inp):
        #
        #  Invoke binascii.b2a_base64 iteratively with
        #  short even length buffers, strip the trailing
        #  line feed from the result and append.  "Even"
        #  means a number that factors to both 6 and 8,
        #  so when it gets to the end of the 8-bit input
        #  there's no partial 6-bit output.
        #
        oup = ''
        while inp:
            if len(inp) > 48:
                t = inp[:48]
                inp = inp[48:]
            else:
                t = inp
                inp = ''
            e = binascii.b2a_base64(t)
            if e:
                oup = oup + e[:-1]
        return oup

    def decode(self, inp):
        if not inp:
            return ''
        return binascii.a2b_base64(inp)




class _IdleCont(object):

    """When process is called, server is in IDLE state
    and will send asynchronous changes."""

    def __init__(self, parent, timeout):
        self.parent = parent
        self.timeout = parent._choose_nonull_or_dflt(IDLE_TIMEOUT, timeout)
        self.parent.idle_timeout = self.timeout + time.time()

    def process(self, data, rqb):
        self.parent.idle_lock.acquire()
        self.parent.idle_rqb = rqb
        self.parent.idle_timeout = self.timeout + time.time()
        self.parent.idle_lock.release()
        if __debug__: self.parent._log(2, 'server IDLE started, timeout in %.2f secs' % self.timeout)
        return None



MonthNames = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

Mon2num = dict(list(zip((x.encode() for x in MonthNames[1:]), list(range(1, 13)))))

InternalDate = re.compile(r'.*INTERNALDATE "'
    r'(?P<day>[ 0123][0-9])-(?P<mon>[A-Z][a-z][a-z])-(?P<year>[0-9][0-9][0-9][0-9])'
    r' (?P<hour>[0-9][0-9]):(?P<min>[0-9][0-9]):(?P<sec>[0-9][0-9])'
    r' (?P<zonen>[-+])(?P<zoneh>[0-9][0-9])(?P<zonem>[0-9][0-9])'
    r'"')


def Internaldate2Time(resp):

    """time_tuple = Internaldate2Time(resp)
    Convert IMAP4 INTERNALDATE to UT."""

    mo = InternalDate.match(resp)
    if not mo:
        return None

    mon = Mon2num[mo.group('mon')]
    zonen = mo.group('zonen')

    day = int(mo.group('day'))
    year = int(mo.group('year'))
    hour = int(mo.group('hour'))
    min = int(mo.group('min'))
    sec = int(mo.group('sec'))
    zoneh = int(mo.group('zoneh'))
    zonem = int(mo.group('zonem'))

    # INTERNALDATE timezone must be subtracted to get UT

    zone = (zoneh*60 + zonem)*60
    if zonen == '-':
        zone = -zone

    tt = (year, mon, day, hour, min, sec, -1, -1, -1)

    utc = time.mktime(tt)

    # Following is necessary because the time module has no 'mkgmtime'.
    # 'mktime' assumes arg in local timezone, so adds timezone/altzone.

    lt = time.localtime(utc)
    if time.daylight and lt[-1]:
        zone = zone + time.altzone
    else:
        zone = zone + time.timezone

    return time.localtime(utc - zone)

Internaldate2tuple = Internaldate2Time   # (Backward compatible)



def Time2Internaldate(date_time):

    """'"DD-Mmm-YYYY HH:MM:SS +HHMM"' = Time2Internaldate(date_time)
    Convert 'date_time' to IMAP4 INTERNALDATE representation."""

    if isinstance(date_time, (int, float)):
        tt = time.localtime(date_time)
    elif isinstance(date_time, (tuple, time.struct_time)):
        tt = date_time
    elif isinstance(date_time, str) and (date_time[0],date_time[-1]) == ('"','"'):
        return date_time        # Assume in correct format
    else:
        raise ValueError("date_time not of a known type")

    if time.daylight and tt[-1]:
        zone = -time.altzone
    else:
        zone = -time.timezone
    return ('"%2d-%s-%04d %02d:%02d:%02d %+03d%02d"' %
            ((tt[2], MonthNames[tt[1]], tt[0]) + tt[3:6] +
             divmod(zone//60, 60)))



FLAGS_cre = re.compile(r'.*FLAGS \((?P<flags>[^\)]*)\)')

def ParseFlags(resp):

    """('flag', ...) = ParseFlags(line)
    Convert IMAP4 flags response to python tuple."""

    mo = FLAGS_cre.match(resp)
    if not mo:
        return ()

    return tuple(mo.group('flags').split())



if __name__ == '__main__':

    # To test: invoke either as 'python imaplib2.py [IMAP4_server_hostname]',
    # or as 'python imaplib2.py -s "rsh IMAP4_server_hostname exec /etc/rimapd"'
    # or as 'python imaplib2.py -l keyfile[:certfile]|: [IMAP4_SSL_server_hostname]'
    #
    # Option "-d <level>" turns on debugging (use "-d 5" for everything)
    # Option "-i" tests that IDLE is interruptible
    # Option "-p <port>" allows alternate ports

    if not __debug__:
        raise ValueError('Please run without -O')

    import getopt, getpass

    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'd:il:s:p:')
    except getopt.error as val:
        optlist, args = (), ()

    debug, debug_buf_lvl, port, stream_command, keyfile, certfile, idle_intr = (None,)*7
    for opt,val in optlist:
        if opt == '-d':
            debug = int(val)
            debug_buf_lvl = debug - 1
        elif opt == '-i':
            idle_intr = 1
        elif opt == '-l':
            try:
                keyfile,certfile = val.split(':')
            except ValueError:
                keyfile,certfile = val,val
        elif opt == '-p':
            port = int(val)
        elif opt == '-s':
            stream_command = val
            if not args: args = (stream_command,)

    if not args: args = ('',)
    if not port: port = (keyfile is not None) and IMAP4_SSL_PORT or IMAP4_PORT

    host = args[0]

    USER = getpass.getuser()

    data = open(os.path.exists("test.data") and "test.data" or __file__).read(1000)
    test_mesg = 'From: %(user)s@localhost%(lf)sSubject: IMAP4 test%(lf)s%(lf)s%(data)s' \
                     % {'user':USER, 'lf':'\n', 'data':data}

    test_seq1 = [
    ('list', ('""', '""')),
    ('list', ('""', '%')),
    ('create', ('imaplib2_test0',)),
    ('rename', ('imaplib2_test0', 'imaplib2_test1')),
    ('CREATE', ('imaplib2_test2',)),
    ('append', ('imaplib2_test2', None, None, test_mesg)),
    ('list', ('', 'imaplib2_test%')),
    ('select', ('imaplib2_test2',)),
    ('search', (None, 'SUBJECT', 'IMAP4 test')),
    ('fetch', ("'1:*'", '(FLAGS INTERNALDATE RFC822)')),
    ('store', ('1', 'FLAGS', '(\Deleted)')),
    ('namespace', ()),
    ('expunge', ()),
    ('recent', ()),
    ('close', ()),
    ]

    test_seq2 = (
    ('select', ()),
    ('response', ('UIDVALIDITY',)),
    ('response', ('EXISTS',)),
    ('append', (None, None, None, test_mesg)),
    ('examine', ()),
    ('select', ()),
    ('fetch', ("'1:*'", '(FLAGS UID)')),
    ('examine', ()),
    ('select', ()),
    ('uid', ('SEARCH', 'SUBJECT', 'IMAP4 test')),
    ('uid', ('SEARCH', 'ALL')),
    ('uid', ('THREAD', 'references', 'UTF-8', '(SEEN)')),
    ('recent', ()),
    )


    AsyncError, M = None, None

    def responder(cb_arg_list):
        response, cb_arg, error = cb_arg_list
        global AsyncError
        cmd, args = cb_arg
        if error is not None:
            AsyncError = error
            M._log(0, '[cb] ERROR %s %.100s => %s' % (cmd, args, error))
            return
        typ, dat = response
        M._log(0, '[cb] %s %.100s => %s %.100s' % (cmd, args, typ, dat))
        if typ == 'NO':
            AsyncError = (Exception, dat[0])

    def run(cmd, args, cb=True):
        if AsyncError:
            M._log(1, 'AsyncError %s' % repr(AsyncError))
            M.logout()
            typ, val = AsyncError
            raise typ(val)
        if not M.debug: M._log(0, '%s %.100s' % (cmd, args))
        try:
            if cb:
                typ, dat = getattr(M, cmd)(callback=responder, cb_arg=(cmd, args), *args)
                M._log(1, '%s %.100s => %s %.100s' % (cmd, args, typ, dat))
            else:
                typ, dat = getattr(M, cmd)(*args)
                M._log(1, '%s %.100s => %s %.100s' % (cmd, args, typ, dat))
        except:
            M._log(1, '%s - %s' % sys.exc_info()[:2])
            M.logout()
            raise
        if typ == 'NO':
            M._log(1, 'NO')
            M.logout()
            raise Exception(dat[0])
        return dat

    try:
        threading.currentThread().setName('main')

        if keyfile is not None:
            if not keyfile: keyfile = None
            if not certfile: certfile = None
            M = IMAP4_SSL(host=host, port=port, keyfile=keyfile, certfile=certfile, ssl_version="tls1", debug=debug, identifier='', timeout=10, debug_buf_lvl=debug_buf_lvl, tls_level="tls_no_ssl")
        elif stream_command:
            M = IMAP4_stream(stream_command, debug=debug, identifier='', timeout=10, debug_buf_lvl=debug_buf_lvl)
        else:
            M = IMAP4(host=host, port=port, debug=debug, identifier='', timeout=10, debug_buf_lvl=debug_buf_lvl)
        if M.state != 'AUTH':   # Login needed
            PASSWD = getpass.getpass("IMAP password for %s on %s: " % (USER, host or "localhost"))
            test_seq1.insert(0, ('login', (USER, PASSWD)))
        M._log(0, 'PROTOCOL_VERSION = %s' % M.PROTOCOL_VERSION)
        if 'COMPRESS=DEFLATE' in M.capabilities:
            M.enable_compression()

        for cmd,args in test_seq1:
            run(cmd, args)

        for ml in run('list', ('', 'imaplib2_test%'), cb=False):
            mo = re.match(r'.*"([^"]+)"$', ml)
            if mo: path = mo.group(1)
            else: path = ml.split()[-1]
            run('delete', (path,))

        if 'ID' in M.capabilities:
            run('id', ())
            run('id', ("(name imaplib2)",))
            run('id', ("version", __version__, "os", os.uname()[0]))
 
        for cmd,args in test_seq2:
            if (cmd,args) != ('uid', ('SEARCH', 'SUBJECT', 'IMAP4 test')):
                run(cmd, args)
                continue

            dat = run(cmd, args, cb=False)
            uid = dat[-1].split()
            if not uid: continue
            run('uid', ('FETCH', uid[-1],
                    '(FLAGS INTERNALDATE RFC822.SIZE RFC822.HEADER RFC822.TEXT)'))
            run('uid', ('STORE', uid[-1], 'FLAGS', '(\Deleted)'))
            run('expunge', ())

        if 'IDLE' in M.capabilities:
            run('idle', (2,), cb=False)
            run('idle', (99,))          # Asynchronous, to test interruption of 'idle' by 'noop'
            time.sleep(1)
            run('noop', (), cb=False)

            run('append', (None, None, None, test_mesg), cb=False)
            num = run('search', (None, 'ALL'), cb=False)[0].split()[0]
            dat = run('fetch', (num, '(FLAGS INTERNALDATE RFC822)'), cb=False)
            M._mesg('fetch %s => %s' % (num, repr(dat)))
            run('idle', (2,))
            run('store', (num, '-FLAGS', '(\Seen)'), cb=False),
            dat = run('fetch', (num, '(FLAGS INTERNALDATE RFC822)'), cb=False)
            M._mesg('fetch %s => %s' % (num, repr(dat)))
            run('uid', ('STORE', num, 'FLAGS', '(\Deleted)'))
            run('expunge', ())
            if idle_intr:
                M._mesg('HIT CTRL-C to interrupt IDLE')
                try:
                    run('idle', (99,), cb=False) # Synchronous, to test interruption of 'idle' by INTR
                except KeyboardInterrupt:
                    M._mesg('Thanks!')
                    M._mesg('')
                    raise
        elif idle_intr:
            M._mesg('chosen server does not report IDLE capability')

        run('logout', (), cb=False)

        if debug:
            M._mesg('')
            M._print_log()
            M._mesg('')
            M._mesg('unused untagged responses in order, most recent last:')
            for typ,dat in M.pop_untagged_responses(): M._mesg('\t%s %s' % (typ, dat))

        print('All tests OK.')

    except:
        if not idle_intr or M is None or not 'IDLE' in M.capabilities:
            print('Tests failed.')

            if not debug:
                print('''
If you would like to see debugging output,
try: %s -d5
''' % sys.argv[0])

            raise
