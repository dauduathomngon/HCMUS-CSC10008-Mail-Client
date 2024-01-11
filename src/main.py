from shell import Shell
from utils import *

if __name__ == "__main__":
    try:
        s = Shell("config.yaml")
        print_greeting()
        s.cmdloop()
    except:
        CONSOLE.print_exception()