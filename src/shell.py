import os
from cmd import Cmd
from tkinter import filedialog
from datetime import datetime
from email.utils import make_msgid
from email.mime.multipart import MIMEMultipart
import time
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

        # tạo cwd = ""
        self.cwd = "~"
        self.__update_prompt()

        # kết nối smtp và pop3
        self.__connect_smtp()
        self.__connect_pop3()

        self.download_mail_thread = threading.Thread(target=self.__get_all_mail)
        self.download_mail_thread.daemon = True  # Đảm bảo luồng kết thúc khi chương trình chính kết thúc
        self.download_mail_thread.start()

    def __update_prompt(self):
        time_now = datetime.now()
        Shell.prompt = f"({time_now.hour}:{time_now.minute}) Cậu đang ở [{self.cwd}] > "

    def __connect_smtp(self):
        # tạo smtp 
        self.smtp = SMTP(self.general_config["MailServer"],
                         self.general_config["SMTP"],
                         debug=False)
        # sau đó connect với server
        self.smtp.connect()

    def __connect_pop3(self):
        # tạo pop3
        self.pop3 = POP3(self.general_config["MailServer"],
                         self.general_config["POP3"],
                         self.general_config["Mail"],
                         self.general_config["Password"],
                         self.filter_config,
                         debug=False) 
        # connect với server
        self.pop3.connect()

    # tải tất cả mail trên server
    def __get_all_mail(self):
        while True:
            with LOCK:
                self.grp_mail_lst = self.pop3.download_emails(self.pop3.user_, self.pop3.passwrd_)
            time.sleep(self.general_config["Autoload"])

    # đóng shell
    def __close(self):
        if self.smtp:
            self.smtp.close()
        if self.pop3:
            self.pop3.close()

    # thoát shell
    def do_exit(self, arg):
        self.__close()
        return True

    # clear màn hình
    def do_clear(self, arg):
        os.system("cls")

    # xuất ra thông tin help
    def do_help(self, arg):
        print_greeting(again=True)

    # liệt kê ra các filter có trong mailbox
    def do_ls(self, arg):
        # nếu vẫn đang ở root => bắt chọn filter trước
        if self.cwd == "~":
            for filter in self.grp_mail_lst:
                CONSOLE.print(f"📂 {filter} ")
        else:
            # đặt lock để tránh trường hợp đang in danh sách mail thì hệ thống down mail về => lỗi
            with LOCK:
                i = 0
                #Duyệt qua từng mail trong filter (được lưu ở cwd)
                for email in self.grp_mail_lst[self.cwd]:
                    i += 1
                    if email["Read Status"] == 0:
                        CONSOLE.print(f"[{i}]📧 [purple][CHƯA ĐỌC][/purple] NGƯỜI GỬI: {email["From"]} || TIÊU ĐỀ: {email["Subject"]}")
                    else:
                        CONSOLE.print(f"[{i}]📧 NGƯỜI GỬI: {email["From"]} || TIÊU ĐỀ: {email["Subject"]}")

    # trỏ đến 1 thư mục filter
    def do_cd(self, arg):
        if arg in self.grp_mail_lst:
            self.cwd = arg
            self.__update_prompt()
        elif arg == "..":
            self.cwd = "~"
            self.__update_prompt()
        else:
            CONSOLE.print("Không tồn tại thư mục: ", arg + "")

    # đọc mail
    def do_read(self, arg):
        with LOCK:
            # xử lí input đầu vào
            arg = int(arg)
            if not arg:
                CONSOLE.print("Chỉ mục của email phải là số, cú pháp đúng: read chỉ_mục_email_cần_đọc ")
            elif self.cwd == "root":
                CONSOLE.print("Cần chọn thư mục cần đọc mail trước. Sử dụng cd tên_thư_mục ")
            elif arg < 1 or arg > len(self.grp_mail_lst[self.cwd]):
                CONSOLE.print("Chỉ mục không hợp lệ! Chỉ mục phải thuộc khoảng 0 -> ", len(self.grp_mail_lst[self.cwd]),"")
            else:
                # đổi trạng thái của mail id.txt trong mailbox
                self.pop3.read_email(self.grp_mail_lst[self.cwd][arg-1])

                # in ra từng thành phần có trong info
                list_info = ["From", "To", "CC", "Subject", "Content", "Attachment"]
                for info in list_info:
                    if info != "" and info != "Attachment":
                        CONSOLE.print(info,": ", self.grp_mail_lst[self.cwd][arg-1][info],"")

                    # nếu là attachment thì in ra danh sách tên
                    elif info == "Attachment":
                        if len(self.grp_mail_lst[self.cwd][arg-1][info]) != 0:
                            CONSOLE.print("Attachment: ")
                            for attachment in self.grp_mail_lst[self.cwd][arg-1][info]:
                                name = attachment["filename"]
                                CONSOLE.print("[",name,"] ")  

                            # Tải email về đường dẫn
                            download = PROMPT.ask("Nhập 1 để tải các file trong mail, 0 để bỏ qua: ")
                            if int(download) == 1:
                                path = filedialog.askdirectory(parent=ROOT)
                                while not os.path.exists(path):
                                    CONSOLE.print("Đường dẫn không hợp lệ. Vui lòng nhập lại.")
                                    path = filedialog.askdirectory(parent=ROOT)
                                for attachment in self.grp_mail_lst[self.cwd][arg-1][info]:
                                    try:
                                        decode_base64_and_save(attachment["attachment_content"], os.path.join(path, attachment["filename"]))
                                    except:
                                        CONSOLE.print_exception()
                                        return
                    
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
            if not check_mail_format(cc):
                CONSOLE.print("[red](ERROR)[/red] Định dạng mail không hợp lệ")
                return
            mail["CC"] = cc

        # tạo bcc (nếu có)
        if "-bcc" in arg_list:
            bcc = PROMPT.ask("[cyan]BCC[/cyan]")
            if not check_mail_format(bcc):
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

            # file không thể vượt quá 3MB
            for file in attachments:
                # đưa bytes về megabytes
                if int(os.stat(file).st_size / float(1 << 20)) > 3:
                    CONSOLE.print("[red](ERROR)[/red] Không thể gửi file lớn hơn 3MB. Vui lòng chọn lại file")
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