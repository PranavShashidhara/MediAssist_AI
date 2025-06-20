import socket
def is_connected(host="8.8.8.8", port=53, timeout=3):
    """
    Check internet connection by trying to connect to DNS server.
    Returns True if connected, False otherwise.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False