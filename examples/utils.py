# Copyright (c) kerem.ai. All Rights Reserved.

import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

ROOT_DIR = Path(__file__).parents[1]
OUTPUTS_DIR = ROOT_DIR / "outputs"

sys.path.append(str(ROOT_DIR))
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def remove_pycache() -> None:
    """
    Remove all __pycache__ directories in the project.
    """
    for path in ROOT_DIR.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)


@contextmanager
def run_example() -> Generator[None, None, None]:
    """
    Run an example and clean up the __pycache__ directories.
    """
    try:
        yield
    except BaseException as e:
        raise e
    finally:
        remove_pycache()


# Exports
__all__ = [
    "ROOT_DIR",
    "OUTPUTS_DIR",
    "remove_pycache",
    "run_example",
]
