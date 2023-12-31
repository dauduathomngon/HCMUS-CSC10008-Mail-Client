from pop3 import POP3
from utils import *

if __name__ == "__main__":
    general_config = process_general(read_config(CONFIG_FILE)["General"])
    filter_config = read_config(CONFIG_FILE)["Filter"]
    pop3 = POP3(general_config["MailServer"], general_config["POP3"], general_config["Mail"], general_config["Password"], filter_config)
    pop3.connect()

    pop3.download_emails(general_config["Mail"], general_config["Password"])
# from shell import Shell
# # from utils import *

# if __name__ == "__main__":
#     try:
#         s = Shell(CONFIG_FILE)
#         #auto_update_mail_thread = threading.Thread(target=(s.__get_mail_lst()))
#         s.cmdloop()
#     except:
#         CONSOLE.print_exception()
#     a = read_config(CONFIG_FILE)["Filter"]
#     print(a[1])