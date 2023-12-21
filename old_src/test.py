from rich import traceback
from shell import Shell
from utils import *

traceback.install()

if __name__ == "__main__":
    app = Shell(DEFAULT.CONFIG_FILE)
    app.cmdloop()