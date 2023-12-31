from shell import Shell
from utils import *

if __name__ == "__main__":
    try:
        s = Shell(CONFIG_FILE)
        # auto_update_mail_thread = threading.Thread(target=s.get_all_mail())
        # auto_update_mail_thread.start()
        s.cmdloop()
    except:
        CONSOLE.print_exception()
