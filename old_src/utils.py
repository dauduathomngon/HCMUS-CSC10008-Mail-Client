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

class DEFAULT:
    TIMEOUT = 10
    MAILSERVER = "127.0.0.1"
    USERNAME = "Tester"
    MAIL = "testing@gmail.com"
    PASSWORD = "123456789"
    SMTP_PORT = 25
    POP3_PORT = 110
    AUTOLOAD = 10

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

    CRLF = "\r\n"

    CONSOLE = console.Console()
    PROMPT = prompt.Prompt()
    ROOT = tkinter.Tk()

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
    general_config = DEFAULT.CONFIG_GENERAL
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
            DEFAULT.CONSOLE.print("[red]ERROR[/red]: Mail ở dạng unicode, vui lòng viết không dấu")
            return False
    return True

def check_mail_format(input: str):
    mails = input.split(',')
    for mail in mails:
        if "@" not in mail:
            return False
        # check xem mail có ở dạng unicode không ? nếu có thì ko hợp lệ
        try:
            mail.encode("ascii")
        except UnicodeEncodeError:
            DEFAULT.CONSOLE.print("[red]ERROR[/red]: Mail ở dạng unicode, vui lòng viết không dấu")
            return False
    return True