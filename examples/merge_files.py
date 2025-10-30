# Copyright (c) kerem.ai. All Rights Reserved.

import argparse
from pathlib import Path

from utils import OUTPUTS_DIR, run_example  # noqa: F401 isort: skip
from src.utils import merge_tif_directory, merge_tif_files  # noqa: F401 isort: skip


def parse_args() -> dict:
    parser = argparse.ArgumentParser("Merge .tif files.")
    parser.add_argument(
        "input_dir", type=str, help="Relative path to the output directory."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="",
        help="Relative path to the output directory.",
    )  # --output-path ""
    parser.add_argument(
        "--delete-after",
        action=argparse.BooleanOptionalAction,
        help="Delete after merging.",
    )  # --delete-after or --no-delete-after
    parser.add_argument(
        "--merging-method",
        type=str,
        choices=["directory", "files"],
        default="directory",
        help="Merging method. (default: directory)",
    )  # --merging-method directory

    return vars(parser.parse_args())


def main(
    input_dir: str, output_path: str | None, delete_after: bool, merging_method: str
) -> None:
    input_dir: Path = OUTPUTS_DIR / input_dir
    assert input_dir.is_dir() and input_dir.exists(), "Input directory must exist."
    if output_path:
        output_path = OUTPUTS_DIR / output_path

    if merging_method == "directory":
        merge_tif_directory(input_dir, output_path, delete_after)
    else:
        if not output_path:
            raise ValueError("Output path is required when merging files.")
        files = list(input_dir.glob("*.tif"))
        merge_tif_files(files, output_path, delete_after)


if __name__ == "__main__":
    with run_example():
        main(**parse_args())
