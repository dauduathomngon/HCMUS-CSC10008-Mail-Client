import os
from cmd import Cmd
from tkinter import filedialog
from datetime import datetime
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart

from smtp import SMTP
from pop3 import POP3
from utils import *

ROOT.withdraw()

class Shell(Cmd):
    def __init__(self, config_path) -> None:
        super(Shell, self).__init__()

        # đọc file confg
        self.general_config = process_general(read_config(config_path)["General"])
        self.filter_config = read_config(config_path)["Filter"]

        # kết nối smtp
        self.__connect_smtp()

    def __connect_smtp(self):
        # tạo smtp 
        self.smtp = SMTP(self.general_config["MailServer"], self.general_config["SMTP"])
        # sau đó connect với server
        self.smtp.connect()
                
    def __close(self):
        if self.smtp:
            self.smtp.close()

    # thoát shell
    def do_exit(self, arg):
        self.__close()
        return True

    # clear màn hình
    def do_clear(self, arg):
        os.system("cls")

    # xuất ra thông tin help
    def do_help(self, arg):
        pass

    # liệt kê ra các mail trong mail box
    def do_ls(self, arg):
        pass

    # thực hiện việc gửi mail
    def do_sendmail(self, arg):
        # tách các argument ra
        arg_list = arg.split(" ")

        # tạo mail
        mail = MIMEMultipart()

        # tạo người gửi
        mail["From"] = self.general_config["Mail"]

        # nhập mail nhận
        to = PROMPT.ask("[cyan]Đến[/cyan]")
        if to == "":
            CONSOLE.print("[red](ERROR)[/red] Không thể để trống mail nhận")
            return
        if not check_mail_format(to):
            CONSOLE.print("[red](ERROR)[/red] Định dạng mail không hợp lệ")
            return
        mail["To"] = to

        # tạo cc (nếu có)
        if "-cc" in arg_list:
            cc = PROMPT.ask("[cyan]CC[/cyan]")
            if not check_mail_format(to):
                CONSOLE.print("[red](ERROR)[/red] Định dạng mail không hợp lệ")
                return
            mail["CC"] = cc

        # tạo bcc (nếu có)
        if "-bcc" in arg_list:
            bcc = PROMPT.ask("[cyan]BCC[/cyan]")
            if not check_mail_format(to):
                CONSOLE.print("[red](ERROR)[/red] Định dạng mail không hợp lệ")
                return
            mail["BCC"] = bcc

        subject = PROMPT.ask("[cyan]Tiêu đề[/cyan]")
        if subject == "":
            CONSOLE.print("[red](ERROR)[/red] Không thể để trống tiêu đề")
            return
        mail["Subject"] = subject

        # tạo ngày gửi
        mail["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

        # tạo nội dung
        content = PROMPT.ask("[cyan]Nội dung[/cyan]")
        mail.attach(MIMEText(content, _subtype = "plain"))

        # tạo các file đính kèm
        if "-a" in arg_list:
            attachments = list(filedialog.askopenfilenames(parent=ROOT))

            # số lượng file không được lớn hơn 5
            if len(attachments) > 5:
                CONSOLE.print("[red](ERROR)[/red] Không thể gửi nhiều hơn 5 file")
                return 

            # file không thể vượt quá 5MB
            for file in attachments:
                # đưa bytes về megabytes
                if int(os.stat(file).st_size / float(1 << 20)) > 5:
                    CONSOLE.print("[red](ERROR)[/red] Không thể gửi file lớn hơn 5MB. Vui lòng chọn lại file")
                    attachments.remove(file)
                    # chọn lại file
                    new_files = list(filedialog.askopenfilenames(parent=ROOT))
                    attachments += new_files

            # in ra những file được đính kèm
            CONSOLE.print("[cyan]File đính kèm[/cyan]")
            for file in attachments:
                CONSOLE.print(f"\t{os.path.basename(file)}")

            # đính kèm file vào mail
            for file in attachments:
                mail.attach(create_file_format(file))

        # tạo message ID
        mail["Message-ID"] = make_msgid()

        # tiến hành gửi mail
        self.smtp.sendmail(mail)

        CONSOLE.print(f"[green](SUCCESS)[/green] Đã gửi thành công mail")