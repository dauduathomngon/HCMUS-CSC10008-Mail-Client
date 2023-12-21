import socket
import traceback
from utils import *

class Protocol:
    # --------------------------------------
    # Constructor
    # --------------------------------------
    def __init__(self, host, port, debug) -> None:
        self.host = host
        self.port = port
        self.debug = debug

        # tạo socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.debug:
            DEFAULT.CONSOLE.print(f"SMTP Socket kết nối với:\n\tHost: {self.host}\n\tPort: {self.port}")

    # --------------------------------------
    # Private Method
    # --------------------------------------
    def get_reply_code(self):
        while True:
            sock_file = self.sock.makefile("rb")

            # đọc response của server từ socket
            line = sock_file.readline().decode()
            line.strip(" \t\r\n")
            if self.debug:
                DEFAULT.CONSOLE.print(f"Server trả lời: \n\t{line[:-1]}")

            # ví dụ: 220 OK
            # code: 220
            # msg: OK
            code = line[:3]

            # xem response của server có valid không
            try:
                code = int(code)
            except ValueError:
                code = -1
                break
            break

        return code

    def send_command(self, cmd, args=""):
        if args != "":
            cmd = f"{cmd} {args}"

        self.sock.sendall(f"{cmd}{DEFAULT.CRLF}".encode("ascii"))
        if self.debug: 
            DEFAULT.CONSOLE.print(f"\nGửi {cmd} command")

    def get_error(self, true_code, fail_msg, true_msg) -> bool:
        if self.get_reply_code() != true_code:
            if self.debug:
                DEFAULT.CONSOLE.print(f"[red]ERROR[/red]: {fail_msg}")
            self.close()
            return False
        else:
            if self.debug:
                DEFAULT.CONSOLE.print(f"[green]SUCCESS[/green]: {true_msg}")
            return True

    def connect(self) -> bool:
        try:
            self.sock.connect((self.host, self.port))
        except Exception:
            DEFAULT.CONSOLE.print(traceback.format_exc())
            self.close()
            return False
        return self.get_error(220,
                              f"Không thể kết nối đến server: {self.host}",
                              f"Đã kết nối thành công đến server: {self.host}")    

    def close(self):
        if self.sock:
            self.sock.close()
        self.sock = None