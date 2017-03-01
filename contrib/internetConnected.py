
import socket
def internetConnected(host="8.8.8.8", port=53, timeout=3):
   """
   Simple function to quickly check, are we connected to the internet.
   Needed to detect when waking up from sleep or returning from suspend.
   Network can take a few seconds to reconnect. Sometimes longer.
   Default connect to host: 8.8.8.8 (google-public-dns-a.google.com)
   OpenPort: 53/tcp
   Service: domain (DNS/TCP)
   Average time to check is less than 0.2 second (200 ms).
   """
   try:
     socket.setdefaulttimeout(timeout)
     socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
     return True
   except Exception as ex:
     print ex.message
     return False
