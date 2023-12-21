from utils import *
from protocol import Protocol

# Tham khảo: https://datatracker.ietf.org/doc/html/rfc1939.html
# Tham khảo: https://github.com/python/cpython/tree/3.12/Lib/poplib.py
class Pop3(Protocol):
    # --------------------------------------
    # Constructor
    # --------------------------------------
    def __init__(self, host, port, debug = True) -> None:
        super().__init__(host, port, debug)

    # --------------------------------------
    # Private Method
    # --------------------------------------

    # --------------------------------------
    # Public method
    # --------------------------------------