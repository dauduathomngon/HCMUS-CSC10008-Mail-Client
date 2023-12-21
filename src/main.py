from shell import Shell
from utils import *

if __name__ == "__main__":
    try:
        s = Shell(CONFIG_FILE)
        s.cmdloop()
    except:
        CONSOLE.print_exception()