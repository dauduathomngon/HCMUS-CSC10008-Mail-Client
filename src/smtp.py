import re
from email.utils import getaddresses
from email.mime.multipart import MIMEMultipart
from protocol import Protocol
from utils import *

# Tham khảo:
# - https://datatracker.ietf.org/doc/html/rfc821
# - https://github.com/python/cpython/blob/main/Lib/smtplib.py
class SMTP(Protocol):
    # --------------------------------------
    # Constructor
    # --------------------------------------
    def __init__(self, host, port, debug = True) -> None:
        super().__init__(host, port, debug)

    # --------------------------------------
    # Method
    # --------------------------------------
    def connect(self):
        # kết nối socket trước
        super().connect()

        # sau đó xem server reply
        code, _ = self.get_reply_msg()
        if code != 220:
            self.close()
            raise Exception(f"Server {self.host} không chấp nhận kết nối")

        if self.debug:
            CONSOLE.print(f"[green](SUCCESS)[/green] SMTP Socket đã kết nối với Server:\n\tHost: {self.host}\n\tPort: {self.port}")

        # gửi command helo
        self.helo()

    def get_reply_msg(self):
        line = super().get_reply_msg()

        # ví dụ: 220 OK
        # code: 220
        # msg: OK
        code = line[:3]
        msg = line[4:]
        
        try:
            code = int(code)
        except: # server reply không đúng format
            code = -1

        return code, msg

    def helo(self):
        self.send_command("HELO", self.host)
        self.check_error_cmd(250, f"HELO {self.host}")

    def mail_from(self, mail_name):
        self.send_command("MAIL FROM:", f"<{mail_name}>")
        self.check_error_cmd(250, f"MAIL FROM: <{mail_name}>")
    
    def rcpt_to(self, mail_name):
        self.send_command("RCPT TO:", f"<{mail_name}>")
        self.check_error_cmd(250, f"RCPT TO: <{mail_name}>")
        
    def data(self):
        self.send_command("DATA")
        self.check_error_cmd(354, "DATA")

    def quit(self):
        self.send_command("QUIT")
        self.check_error_cmd(221, "QUIT")

    def sendmsg(self,
                mail_from: str,
                mail_to: list[str],
                b_msg: bytes):

        # đầu tiên gửi command MAIL FROM
        self.mail_from(mail_from)

        # tiếp theo gửi command RCPT TO cho từng mail trong mail to
        for mail in mail_to:
            self.rcpt_to(mail)

        # tiếp theo là gửi command data
        self.data()

        # cuối cùng là gửi message
        try:
            self.sock.sendall(b_msg)
        except Exception as e:
            raise Exception(f"Server {self.host} không nhận message") from e

        # sau khi gửi message xong thì ta sẽ skip reply từ server gửi về
        super().get_reply_msg()
        
        # sau đó reset server
        self.quit()
        
        # sau đó reconnect server
        self.close()
        self.connect()

    def sendmail(self, mail: MIMEMultipart):
        # lấy mail gửi
        mail_from = getaddresses([mail["From"]])[0][1]

        # lấy tất cả mail nhận
        mail_to = []
        for field in (mail["To"], mail["CC"], mail["BCC"]):
            if field is not None:
                mail_to += [addr[1] for addr in getaddresses([field])]

        # xoá đi BCC
        del mail["BCC"]

        # format lại mail
        msg = mail.as_string()
        # tham khảo: https://github.com/python/cpython/blob/103c4ea27464cef8d1793dab347f5ff3629dc243/Lib/smtplib.py#L179
        msg = re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, msg)

        # sau đó đưa về dạng bytes
        b_msg = msg.encode("ascii")
        # tham khảo: https://github.com/python/cpython/blob/103c4ea27464cef8d1793dab347f5ff3629dc243/Lib/smtplib.py#L176
        b_msg = re.sub(br'(?m)^\.', b'..', b_msg)

        # theo RFC 821 quy định
        # phần cuối của message phải có dạng
        # CRLF.CRLF
        if b_msg[-2:] != BCRLF:
            b_msg += BCRLF
        b_msg += b"." + BCRLF

        # và cuối cùng tiến hành gửi mail
        self.sendmsg(mail_from, mail_to, b_msg)