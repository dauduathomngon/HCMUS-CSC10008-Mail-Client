import socket
import io
import traceback
from email.mime.multipart import MIMEMultipart
from email import generator
from email import utils

from utils import *

# Tham khảo: https://github.com/python/cpython/blob/main/Lib/smtplib.py
class SMTP:
    # --------------------------------------
    # Constructor
    # --------------------------------------
    def __init__(self, host, port, debug = False) -> None:
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
    def __get_reply_code(self):
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

    def __send_command(self, cmd, args=""):
        if args != "":
            cmd = f"{cmd} {args}"

        self.sock.sendall(f"{cmd}{DEFAULT.CRLF}".encode("ascii"))
        if self.debug: 
            DEFAULT.CONSOLE.print(f"\nGửi {cmd} command")

    def __get_error(self, true_code, fail_msg, true_msg) -> bool:
        if self.__get_reply_code() != true_code:
            if self.debug:
                DEFAULT.CONSOLE.print(f"[red]ERROR[/red]: {fail_msg}")
            self.close()
            return False
        else:
            if self.debug:
                DEFAULT.CONSOLE.print(f"[green]SUCCESS[/green]: {true_msg}")
            return True

    def __connect(self) -> bool:
        try:
            self.sock.connect((self.host, self.port))
        except Exception:
            DEFAULT.CONSOLE.print(traceback.format_exc())
            self.close()
            return False
        return self.__get_error(220,
                                f"Không thể kết nối đến server: {self.host}",
                                f"Đã kết nối thành công đến server: {self.host}")

    def __send_helo_command(self) -> bool:
        self.__send_command("HELO", self.host)
        return self.__get_error(250,
                                f"Không gửi được HELO command đến server", 
                                f"Đã gửi thành công HELO command đến server")

    def __init_sender(self, mail_name) -> bool:
        self.__send_command("MAIL FROM:", mail_name)
        return self.__get_error(250,
                                f"Không gửi được MAIL_FROM: {mail_name} command đến server",
                                f"Đã gửi thành công MAIL_FROM: {mail_name} command đến server")

    def __init_receiver(self, mail_name) -> bool:
        self.__send_command("RCPT TO:", mail_name)
        return self.__get_error(250,
                                f"Không gửi được RCPT TO: {mail_name} command đến server",
                                f"Đã gửi thành công RCPT TO: {mail_name} command đến server")

    def __init_data(self) -> bool:
        self.__send_command("DATA")
        return self.__get_error(354,
                                f"Không gửi được DATA command đến server",
                                f"Đã gửi thành công DATA command đến server")

    def __send_mail(self, 
                  mail_from: str,
                  mail_to: list[str],
                  msg):
        if not self.__init_sender(mail_from):
            return

        for mail in mail_to:
            if not self.__init_receiver(mail):
                return

        if not self.__init_data():
            return

        # message cần có <CRLF>.<CRLF> thì mởi gửi được 
        # mà ta đã thêm một CRLF vào trước đó nên ta chỉ cần thêm .<CRLF> nữa
        msg = msg + b"." + bytes(DEFAULT.CRLF, "utf-8")

        # gửi message
        self.sock.sendall(msg)

        # check xem đã gửi thành công chưa
        if not self.__get_error(250, 
                            f"Không gửi được message đến server",
                            f"Đã gửi thành công message đến server"):
            return

    # --------------------------------------
    # Public Method
    # --------------------------------------
    def create_connection(self) -> bool:
        return (self.__connect() and 
                self.__send_helo_command())

    def send(self, mail: MIMEMultipart):
        # lấy mail nhận
        mail_from = utils.getaddresses([mail["From"]])[0][1]

        # lấy tất cả mail gửi
        mail_to = []
        for field in (mail["To"], mail["CC"], mail["BCC"]):
            if field is not None:
                mail_to += [addr[1] for addr in utils.getaddresses([field])]

        # xoá đi BCC bởi vì To, CC không nhìn thấy BCC
        del mail["BCC"]

        # BytesGenerator cần một object bytes có method write() do đó ta dùng BytesIO
        msg_bytes = io.BytesIO()
        gen = generator.BytesGenerator(msg_bytes)
        gen.flatten(mail, linesep = "\r\n")

        send_msg = msg_bytes.getvalue()

        # nếu hai char cuối không phải là CRLF thì ta thêm vào
        send_msg = send_msg + bytes(DEFAULT.CRLF, "utf-8")
        
        # tiến hành gửi mail
        self.__send_mail(mail_from, mail_to, msg_bytes.getvalue())

    def close(self):
        if self.sock:
            self.sock.close()
        self.sock = None