import socket
from utils import *
from icecream import ic

class Protocol:
    # --------------------------------------
    # Constructor
    # --------------------------------------
    def __init__(self, host, port, debug) -> None:
        self.host = host
        self.port = port

        # in ra các thông tin debug
        self.debug = debug

        # lưu giữ reply của server gửi về cho socket
        self.file = None

        # tạo socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # đặt timeout
        self.sock.settimeout(TIMEOUT)

    # --------------------------------------
    # Method
    # --------------------------------------
    def connect(self):
        """
        Thực hiện kết nối với server
        """
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(TIMEOUT)

        try:
            if self.debug:
                CONSOLE.print("Tiến hành kết nối đến Server...")
            self.sock.connect((self.host, self.port))
        except Exception as e:
            self.close()
            raise Exception(f"Không thể kết nối đến Server:\n\tHost: {self.host}\n\tPort:{self.port}") from e

    def close(self):
        """
        Đóng socket
        """
        if self.sock:
            self.sock.close()
        self.sock = None
        self.file = None

    def send_command(self, cmd, args=""):
        """Gửi command đến Server đã kết nối

        Args:
            cmd (str): tên command
            args (str, optional): các tham số của command. Mặc định là "".
        """
        if args != "":
            cmd = f"{cmd} {args}"

        if self.debug:
            CONSOLE.print(f"Tiến hành gửi command {cmd}...")

        try:
            self.sock.sendall(f"{cmd}{CRLF}".encode("ascii"))
        except OSError as e:
            self.close()
            raise Exception(f"Server bị mất kết nối") from e
            
    def get_reply_msg(self):
        """
        Khi mà gửi command đến server, server sẽ reply code về, ta phải lấy code đó và kiểm tra nó 
        """
        if self.file is None:
            self.file = self.sock.makefile("rb")

        # đọc reply của server
        try:
            line = self.file.readline(MAXLINE + 1).decode()
            line = line.strip(" \t\r\n")
        except OSError as e:
            self.close()
            raise Exception(f"Server bị mất kết nối") from e

        return line

    def check_error_cmd(self, true_code, cmd, get_msg=False):
        """Xem thử có bị lỗi với message được server reply về không

        Args:
            true_code (int): giá trị code đúng mà ta muốn nhận
            cmd (str): command mà ta đã gửi
        """
        code, msg = self.get_reply_msg()

        if code != true_code:
            self.close()
            raise Exception(f"Server trả về {cmd} với lỗi {code} {msg}")

        if self.debug:
            CONSOLE.print(f"[green](SUCCESS)[/green] Gửi thành công command {cmd} đến Server\n")
        
        if get_msg:
            return msg
        else:
            return None