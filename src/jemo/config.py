from yaml import Loader, load


def load_config_file(config_file_path: str) -> dict:
    with open(config_file_path, "r", encoding="utf8") as config_file:
        return load(config_file, Loader)
