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
                 user, passwrd, filter_config,
                 debug = True) -> None:
        super().__init__(host, port, debug)
        self.user_ = user
        self.passwrd_ = passwrd
        self.filter_config = filter_config

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
    
    def uidl(self):
        self.send_command("UIDL")
        self.check_error_cmd("+OK", f"UIDL")
        # reply sẽ là ID của file được lưu trên server, ví dụ 3627635761526.msg
        return self.get_remain_msg()
    
    def quit(self):
        self.send_command("UIDL")
        self.check_error_cmd("+OK", f"QUIT")

    def capa(self):
        self.send_command("CAPA")
        self.check_error_cmd("+OK", f"CAPA")
        temp = self.get_remain_msg()

    # kiểm tra 1 email đã được đọc hay chưa
    def is_read(self, email):
        directory = os.path.join(os.getcwd(), ".." , "mailbox", self.user_, email["Filter"], email["ID"])
        email_file_name = email["ID"] + ".txt"
        # đọc trong thư mục user xem có mail đó không, nếu có thì đọc kí tự đầu tiên
        # tương ứng với trạng thái đã đọc hay chưa của
        for root, dirs, files in os.walk(directory):
            if email_file_name in files:
                email_file_path = os.path.join(root, email_file_name)
                with open(email_file_path, "r") as f:
                    read_status = int(f.read(1))
                    return read_status
        return 0 
    # filter 1 email, trả về chuỗi là loại của email đó
    def filter_email(self, email):
        for line in self.filter_config:
            attr, mail_type = line.keys()
            if attr == "Spam":
                for evidence in line[attr]:
                    if evidence.lower() in email["Subject"].lower() or evidence in email["Content"].lower():
                        return line[mail_type]
            else:
                for evidence in line[attr]:
                    if evidence.lower() in email[attr]:
                        return line[mail_type]
        return "Inbox"
    # đọc 1 email, cập nhật lại bit đã đọc trong file txt = 1
    def read_email(self, email):
        
        directory = os.path.join(os.getcwd(), ".." , "mailbox", self.user_, email["Filter"], email["ID"])
        email_file_name = email["ID"] + ".txt"
        for root, dirs, files in os.walk(directory):
            if email_file_name in files:
                email_file_path = os.path.join(root, email_file_name)
                with open(email_file_path, "w") as f:
                    f.write("1")
    # truyền vào idx và id của 1 email, gọi retr để down email về và xử lí, lưu vào dict               
    def extract_mail(self, idx, id):
        # lấy tất cả thông tin và nội dung của mail
        raw_mail = self.retr(idx)
        email = dict()
        email["ID"] = id
        email["Attachment"] = []
        email["boundary"] = ""
        email["CC"] = ""
        email["To"] = ""

        i = 0
        # duyệt qua từng dòng trong nội dung mail, trích xuất các thông tin tương ứng
        while i < len(raw_mail) - 1:
            if "From:" in raw_mail[i]:
                email["From"] = raw_mail[i].split("From:")[-1]

            elif "To:" in raw_mail[i]:
                email["To"] = raw_mail[i].split("To:")[-1]
                
            elif "Subject:" in raw_mail[i]:
                email["Subject"] = raw_mail[i].split("Subject:")[-1]
                  
            elif "Date:" in raw_mail[i]:
                email["Date"] = raw_mail[i].split("Date:")[-1]
                
            elif "CC:" in raw_mail[i]:
                email["CC"] = raw_mail[i].split("CC:")[-1]
                
            elif "boundary=" in raw_mail[i]:
                email["boundary"] = raw_mail[i].split("boundary=")[-1][1:-1]
   
            # nếu gặp content-tyoe => bắt đầu phần nội dung hoặc attachment
            elif "Content-Type:" in raw_mail[i]:
                while True:
                    # phần nội dung của mail sẽ có text/plain dòng đầu tiên 
                    if "text/plain" in raw_mail[i]:
                        content = []
                        # giữa phần header của và nội dung là 1 dấu \n, duyệt while để bỏ qua những
                        # dòng chứa thông tin không quan trọng 
                        while raw_mail[i] != "":
                            i += 1
                        # từ vị trí khoảng trắng đến boundary (nếu có) tiếp theo sẽ là nội dung email
                        while i < len(raw_mail) and (email["boundary"] == "" or email["boundary"] not in raw_mail[i]):
                            content.append(raw_mail[i])
                            i += 1
                        email["Content"] = "".join(content)
                        # thoát để chuyện sang cụm boundary tiếp theo.
                        break 
                    else:
                        # không phải content => attachment
                        attachment = {}
                        for attr in ["Type:", "filename=", "Content-Transfer-Encoding:"]:
                            j = i
                            while attr not in raw_mail[j] and j < len(raw_mail) - 1:
                                j += 1
                            attachment[attr.replace(":", "").replace("-", "_").replace("=","").lower()] = raw_mail[j].split(attr)[-1].replace("\"", "")

                        # nội dung của file sẽ đọc từ "" đến boundary
                        attachment["attachment_content"] = []
                        while raw_mail[i] != "":        
                            i += 1
                        while email["boundary"] not in raw_mail[i]:
                            attachment["attachment_content"].append(raw_mail[i])  
                            i += 1      
                        attachment["attachment_content"] = "".join(attachment["attachment_content"])             
                        email["Attachment"].append(attachment)
                        break
            i += 1
        return email
    # gọi tất cả những bước trên.         
    def download_emails(self, user, password):     
        self.capa()

        # kiểm tra user
        self.user()

        # kiểm tra password
        self.passwrd()

        # lấy stat của mail
        self.stat()

        # lấy list các mail có trong mail
        list_email = self.uidl()

        usr_path = os.path.join(os.getcwd(),'..', 'mailbox', user)
        if not os.path.exists(usr_path):
            os.makedirs(usr_path)

        lst_extracted_emails = []
        # duyệt qua từng file, kiểm tra những file nào chưa đọc thì tải xuống
        for email in list_email:
            email_idx, email_id = email.split(" ")[0], email.split(" ")[1].split(".")[0]
            extracted_email = self.extract_mail(email_idx, email_id)
            extracted_email["Filter"] = self.filter_email(extracted_email)
            extracted_email["Read Status"] = self.is_read(extracted_email)
            lst_extracted_emails.append(extracted_email)

            email_path = os.path.join(usr_path, extracted_email["Filter"], email_id)
            # nếu đã có file => mail đã được tải
            if os.path.exists(email_path):
                continue
            # nếu chưa có file => tạo file chứa trạng thái của mail
            os.makedirs(os.path.join(email_path))
            with open(os.path.join(email_path, email_id + ".txt") , "w") as file:
                # từ email index, tải mail về từ mail server và trích xuất các thông tin tương ứng
                # ghi giá trị mặc định 0 (chưa đọc) vào file txt
                file.write("0")
                for attachment in extracted_email["Attachment"]:
                    attachment_path = os.path.join(email_path, attachment["filename"])
                    decode_base64_and_save(attachment["attachment_content"], attachment_path)
        
        filter_groups = dict()
        for email in lst_extracted_emails:
            filter_groups[email["Filter"]] = []
        for email in lst_extracted_emails:
            filter_groups[email["Filter"]].append(email)
            
        return filter_groups
                
        



                
            














    



        

        
