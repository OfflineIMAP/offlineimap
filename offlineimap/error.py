class OfflineImapError(Exception):
    """An Error during offlineimap synchronization"""

    class ERROR:
        """Severity level of an Exception

        * **MESSAGE**:  Abort the current message, but continue with folder
        * **FOLDER_RETRY**: Error syncing folder, but do retry
        * **FOLDER**:   Abort folder sync, but continue with next folder
        * **REPO**:     Abort repository sync, continue with next account
        * **CRITICAL**: Immediately exit offlineimap
        """

        MESSAGE, FOLDER_RETRY, FOLDER, REPO, CRITICAL = 0, 10, 15, 20, 30

    def __init__(self, reason, severity, errcode=None):
        """
        :param reason: Human readable string suitable for logging

        :param severity: denoting which operations should be
               aborted. E.g. a ERROR.MESSAGE can occur on a faulty
               message, but a ERROR.REPO occurs when the server is
               offline.

        :param errcode: optional number denoting a predefined error
               situation (which let's us exit with a predefined exit
               value). So far, no errcodes have been defined yet.

        :type severity: OfflineImapError.ERROR value"""

        self.errcode  = errcode
        self.severity = severity

        # 'reason' is stored in the Exception().args tuple.
        super(OfflineImapError, self).__init__(reason)

    @property
    def reason(self):
        return self.args[0]
