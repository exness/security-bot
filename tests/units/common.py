import pathlib


def get_test_root_directory():
    return pathlib.Path(__file__).parent.parent.resolve()
