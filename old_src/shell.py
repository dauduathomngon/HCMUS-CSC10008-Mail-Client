import os
from cmd import Cmd
from tkinter import filedialog
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from smtp import SMTP
from utils import *

DEFAULT.ROOT.withdraw()

class Shell(Cmd):
    def __init__(self, config_path) -> None:
        super(Shell, self).__init__()

        # đọc file confg
        self.general_config = process_general(read_config(config_path)["General"])
        self.filter_config = read_config(config_path)["Filter"]

        # tạo smtp connection
        self.smtp = SMTP(self.general_config["MailServer"], self.general_config["SMTP"])

        if not self.smtp.create_connection(self.general_config["Mail"]):
            DEFAULT.CONSOLE.print(f"[red]ERROR:[/red] Không thể kết nối đến Server: {self.general_config['MailServer'], self.general_config['SMTP']}")
            self.__close()
            raise Exception(f"Không thể kết nối đến Server: {self.general_config['MailServer'], self.general_config['SMTP']}")

    def __close(self):
        self.smtp.close()

    def do_exit(self, arg):
        """
        Thoát shell
        """
        self.__close()
        return True

    def do_clear(self, arg):
        """ 
        Clear màn hình
        """
        os.system("cls")

    def do_help(self, arg):
        """
        Xuất ra thông tin help
        """
        pass

    def do_ls(self, arg):
        """
        Liệt kê những folder chứa hộp thư
        """
        pass

    def do_setdebug(self, arg):
        if arg == "-t":
            self.smtp.debug = True
        elif arg == "-f":
            self.smtp.debug = False

    def do_sendmail(self, arg):
        """
        Thực hiện việc gửi mail
        """
        # tách các argument
        arg_list = arg.split(" ")

        # nhập mail
        to = DEFAULT.PROMPT.ask("[cyan]Đến[/cyan]")
        if to == "":
            DEFAULT.CONSOLE.print("[red]ERROR[/red]: Không thể để trống mail nhận")
            return
        if not check_mail_format(to):
            DEFAULT.CONSOLE.print("[red]ERROR[/red]: Định dạng mail không hợp lê")
            return

        # tạo mail
        mail = MIMEMultipart()

        # tạo người gửi và nơi nhận mail
        mail["From"] = self.general_config["Mail"]
        mail["To"] = to

        # tạo cc (nếu có)
        if "-cc" in arg_list:
            cc = DEFAULT.PROMPT.ask("[cyan]CC[/cyan]")
            if not check_mail_format(to):
                DEFAULT.CONSOLE.print("[red]ERROR[/red]: Định dạng mail không hợp lê")
                return
            mail["BCC"] = bcc

        # tạo bcc (nếu có)
        if "-bcc" in arg_list:
            bcc = DEFAULT.PROMPT.ask("[cyan]BCC[/cyan]")
            if not check_mail_format(to):
                DEFAULT.CONSOLE.print("[red]ERROR[/red]: Định dạng mail không hợp lê")
                return
            mail["CC"] = cc

        # tạo tiêu đề
        subject = DEFAULT.PROMPT.ask("[cyan]Tiêu đề[/cyan]")
        if subject == "":
            DEFAULT.CONSOLE.print("[red]ERROR[/red]: Không thể để trống tiêu đề")
            return
        mail["Subject"] = subject

        # tạo ngày gửi
        mail["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S")

        # tạo nội dung
        content = DEFAULT.PROMPT.ask("[cyan]Nội dung[/cyan]")
        mail.attach(MIMEText(content, "plain"))

        # tạo các file đính kèm
        if "-a" in arg_list:
            attachments = list(filedialog.askopenfilenames(parent=DEFAULT.ROOT))

            # số lượng file không được lớn hơn 5
            if len(attachments) > 5:
                DEFAULT.CONSOLE.print("[red]ERROR[/red]: Không thể gửi nhiều hơn 5 file")
                return 

            # file không thể vượt quá 5MB
            for file in attachments:
                # đưa bytes về megabytes
                if int(os.stat(file).st_size / float(1 << 20)) > 5:
                    DEFAULT.CONSOLE.print("[red]ERROR[/red]: Không thể gửi file lớn hơn 5MB. Vui lòng chọn lại file")
                    attachments.remove(file)
                    # chọn lại file
                    new_files = list(filedialog.askopenfilenames(parent=DEFAULT.ROOT))
                    attachments += new_files

            # in ra những file được đính kèm
            DEFAULT.CONSOLE.print("[cyan]File đính kèm:[/cyan]")
            for file in attachments:
                DEFAULT.CONSOLE.print(f"\t{os.path.basename(file)}")

            # đính kèm file vào mail
            for file in attachments:
                mail.attach(create_file_format(file))

        # tiến hành gửi mail
        self.smtp.send(mail)
