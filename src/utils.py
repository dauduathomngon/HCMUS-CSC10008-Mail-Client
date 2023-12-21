import os
import yaml
from rich import prompt, console
import tkinter
import mimetypes
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders

# -----------------------------
# Const values
# -----------------------------
MAILSERVER = "127.0.0.1"
USERNAME = "Nguyen"
MAIL = "lntesting@gmail.com"
PASSWORD = "123456789"
SMTP_PORT = 2225
POP3_PORT = 3335
AUTOLOAD = 10

TIMEOUT = 10
CRLF = "\r\n"
BCRLF = b"\r\n"
MAXLINE = 2049

CONFIG_FILE = "config.yaml"

CONFIG_GENERAL = {"Autoload": AUTOLOAD, 
                  "MailServer": MAILSERVER,
                  "POP3": POP3_PORT,
                  "Password": PASSWORD,
                  "SMTP": SMTP_PORT,
                  "Username": USERNAME,
                  "Mail": MAIL}

CONFIG_FILTER = {"From": {"Value": None,
                          "To": None},
                 "Subject": {"Value": None,
                             "To": None},
                 "Content": {"Value": None,
                             "To": None},
                 "Spam": {"Value": None,
                          "To": None}}

CONSOLE = console.Console()
PROMPT = prompt.Prompt()
ROOT = tkinter.Tk()

TYPE = {"image": MIMEImage,
        "text": MIMEText,
        "audio": MIMEAudio}

# -----------------------------
# Helper function
# -----------------------------
def read_config(path):
    with open(path, "r") as file:
        return yaml.safe_load(file)
    
def process_general(client_general: dict) -> dict:
    """
    Xử lý input của file config để đưa về dạng chuẩn như sau 
    (nếu file config không có các phần tương ứng thì sẽ dùng mặc định)
        Username
        Password
        Mail
        MailServer
        SMTP
        POP3
        Autoload
    """
    general_config = CONFIG_GENERAL
    same_config = set(client_general.keys()).intersection(set(general_config.keys()))   

    # nếu không có Mail trong config file thì mail có thể để ở Username
    if "Mail" not in same_config:
        if "Username" in same_config:
            mail_name = client_general["Username"].split("<", 1)[1].split(">")[0]
            user_name = client_general["Username"].split("<", 1)[0].rstrip()
            client_general["Username"] = user_name
            client_general["Mail"] = mail_name

    for key in general_config.keys():
        if key in set(client_general.keys()):
            general_config[key] = client_general[key]

    # xem email hợp lệ không (có dấu @)
    if "@" not in general_config["Mail"]:
        raise Exception("This is not valid email")

    return general_config

def check_mail_format(input: str):
    mails = input.split(',')
    for mail in mails:
        if "@" not in mail:
            return False
        # check xem mail có ở dạng unicode không ? nếu có thì ko hợp lệ
        try:
            mail.encode("ascii")
        except UnicodeEncodeError:
            CONSOLE.print("[red]ERROR[/red]: Mail ở dạng unicode, vui lòng viết không dấu")
            return False
    return True

def create_file_format(file):
    """
    Tham khảo: https://github.com/dros1986/EmailClient/blob/master/supermail/EmailClient.py#L137
    """
    type, encoding = mimetypes.guess_type(file)

    if type is None or encoding is not None:
        type = "application/octet-stream"

    # ví dụ: content_type = "image/png"
    # file_type = "image"
    # file_ext = "png"
    file_type, file_ext = type.split('/', 1)
    with open(file, "rb") as f:
        if file_type not in set(TYPE.keys()):
            msg = MIMEBase(file_type, file_ext)
            msg.set_payload(f.read())
        else:
            msg = TYPE[file_type](f.read(), _subtype = file_ext)

    file_name = os.path.basename(file)
    encoders.encode_base64(msg)
    msg.add_header('Content-Disposition', 'attachment', filename = file_name)
    return msg