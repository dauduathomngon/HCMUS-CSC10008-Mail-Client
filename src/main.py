from pop3 import POP3
from utils import *

if __name__ == "__main__":
    general_config = process_general(read_config(CONFIG_FILE)["General"])
    filter_config = read_config(CONFIG_FILE)["Filter"]
    pop3 = POP3(general_config["MailServer"], general_config["POP3"], general_config["Mail"], general_config["Password"])
    pop3.connect()

    pop3.download_mail(general_config["Mail"], general_config["Password"])
# from shell import Shell
# from utils import *

# if __name__ == "__main__":
#     try:
#         s = Shell(CONFIG_FILE)
#         s.cmdloop()
#     except:
#         CONSOLE.print_exception()