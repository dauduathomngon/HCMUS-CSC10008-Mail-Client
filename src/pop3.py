from protocol import Protocol
from utils import *

# Tham khảo: 
# - https://datatracker.ietf.org/doc/html/rfc1939.html
# - https://github.com/python/cpython/tree/3.12/Lib/poplib.py
class POP3(Protocol):
    # --------------------------------------
    # Constructor
    # --------------------------------------
    def __init__(self, host, port,
                 user, passwrd,
                 debug = True) -> None:
        super().__init__(host, port, debug)
        self.user_ = user
        self.passwrd_ = passwrd

    # --------------------------------------
    # Method
    # --------------------------------------
    def connect(self):
        # kết nối socket trước
        super().connect()

        # sau đó xem server reply
        code, _ = self.get_reply_msg()

        if code != "+OK":
            self.close()
            raise Exception(f"Server {self.host} không chấp nhận kết nối")

        if self.debug:
            CONSOLE.print(f"[green](SUCCESS)[/green] SMTP Socket đã kết nối với Server:\n\tHost: {self.host}\n\tPort: {self.port}\n")

    def get_reply_msg(self):
        line = super().get_reply_msg()

        if "+" not in line and "-" not in line:
            raise Exception("Server reply không đúng format")

        code = line.split(" ", 1)
        if len(code) == 1:
            return code[0], ""
        else:
            return code[0], code[1]

    def get_remain_msg(self):
        lines = []
        while True:
            line = super().get_reply_msg()
            if line == ".":
                break
            lines.append(line)
        return lines

    def user(self):
        self.send_command("USER", self.user_)
        self.check_error_cmd("+OK", f"USER {self.user_}")

    def passwrd(self):
        self.send_command("PASS", self.passwrd_)
        self.check_error_cmd("+OK", f"PASS {self.passwrd_}")

    def stat(self):
        self.send_command("STAT")
        if self.debug:
            msg = self.check_error_cmd("+OK", f"STAT", get_msg=True).split(" ", 1)
            CONSOLE.print(f"Mailbox {self.host}: {self.user_} gồm {int(msg[0])} mail và có tổng cộng {int(msg[1])} bytes\n")
        else:
            self.check_error_cmd("+OK", f"STAT")

    def lst(self):
        self.send_command("LIST")
        self.check_error_cmd("+OK", f"LIST")
        # đối với các command như LIST, thì server vẫn còn reply những dòng phía dưới
        # và những reply đó là thông tin về message bao gồm idx và bytes
        return self.get_remain_msg()

    def retr(self, idx):
        self.send_command("RETR", idx)
        self.check_error_cmd("+OK", f"RETR {idx}")
        # các reply còn lại của command RETR là thông tin về email
        # và ta sẽ xử lý đoạn này sau
        return self.get_remain_msg()