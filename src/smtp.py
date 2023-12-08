import io
from email.mime.multipart import MIMEMultipart
from email import generator
from email import utils

from protocol import Protocol
from utils import *

# Tham khảo: https://github.com/python/cpython/blob/main/Lib/smtplib.py
class SMTP(Protocol):
    # --------------------------------------
    # Constructor
    # --------------------------------------
    def __init__(self, host, port, debug = True) -> None:
        super().__init__(host, port, debug)

    # --------------------------------------
    # Private Method
    # --------------------------------------
    def __send_helo_command(self) -> bool:
        self.send_command("HELO", self.host)
        return self.get_error(250,
                                f"Không gửi được HELO command đến server", 
                                f"Đã gửi thành công HELO command đến server")

    def __init_sender(self, mail_name) -> bool:
        self.send_command("MAIL FROM:", mail_name)
        return self.get_error(250,
                                f"Không gửi được MAIL_FROM: {mail_name} command đến server",
                                f"Đã gửi thành công MAIL_FROM: {mail_name} command đến server")

    def __init_receiver(self, mail_name) -> bool:
        self.send_command("RCPT TO:", mail_name)
        return self.get_error(250,
                                f"Không gửi được RCPT TO: {mail_name} command đến server",
                                f"Đã gửi thành công RCPT TO: {mail_name} command đến server")

    def __init_data(self) -> bool:
        self.send_command("DATA")
        return self.get_error(354,
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
        if not self.get_error(250, 
                            f"Không gửi được message đến server",
                            f"Đã gửi thành công message đến server"):
            return

    # --------------------------------------
    # Public method
    # --------------------------------------
    def create_connection(self) -> bool:
        return (self.connect() and 
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