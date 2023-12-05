import yaml
from icecream import ic

def open_config(path: str):
    with open(path, "r") as file:
        return yaml.safe_load(file)

ic(open_config("config.yaml"))