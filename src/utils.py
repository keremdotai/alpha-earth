# Copyright (c) kerem.ai. All Rights Reserved.

import shutil
from pathlib import Path

import rasterio
from rasterio.merge import merge


def is_notebook() -> bool:
    """
    Check if the code is running in a Jupyter notebook or IPython environment.

    Returns
    -------
    bool:
        True if running in a notebook/IPython, False otherwise.
    """
    try:
        # Check if we're in IPython/Jupyter environment
        from IPython import get_ipython

        ipython = get_ipython()

        # If we have an IPython instance, check if it's a notebook
        if ipython is not None:
            # Check if we're in a notebook by looking at the class name
            if "IPKernelApp" in str(type(ipython)):
                return True
            # Alternative check for notebook environment
            if hasattr(ipython, "kernel") and ipython.kernel is not None:
                return True
        return False
    except BaseException:
        return False


def merge_tif_directory(
    input_dir: str | Path,
    output_path: str | Path | None = None,
    delete_after: bool = False,
) -> None:
    """
    Merge all .tif files in the input directory into a single .tif file.

    Parameters
    ----------
    input_dir:
        Path to the input directory containing the .tif files.
    output_path:
        Path to the output .tif file.
    delete_after:
        Whether to delete the source files after merging.
    """
    input_dir = Path(input_dir)
    assert input_dir.is_dir(), "Input directory must exist."
    files = list(input_dir.glob("*.tif"))

    if output_path is None:
        output_path = input_dir.with_suffix(".tif")

    # Merge the files
    merge_tif_files(files, output_path, delete_after)

    # Remove the input directory if requested
    if delete_after:
        shutil.rmtree(input_dir)


def merge_tif_files(
    files: list[str | Path], output_path: str | Path, delete_after: bool = False
) -> None:
    """
    Merge a list of .tif files into a single .tif file.

    Parameters
    ----------
    files:
        List of paths to the .tif files to merge.
    output_path:
        Path to the output .tif file.
    delete_after:
        Whether to delete the source files after merging.
    """
    files = [Path(file) for file in files]
    assert all(
        file.is_file() and file.suffix == ".tif" and file.exists() for file in files
    ), "All files must exist and be .tif files."
    assert len(files) > 0, "No files to merge."

    # Merge source files
    srcs = [rasterio.open(file) for file in files]
    merged, out_trans = merge(srcs)

    profile: dict = srcs[0].profile
    profile.update(
        {
            "height": merged.shape[1],
            "width": merged.shape[2],
            "transform": out_trans,
        }
    )

    # Save merged file
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(merged)

    # Close the opened files
    for src in srcs:
        src.close()

    # Remove the source files if requested
    if delete_after:
        for file in files:
            file.unlink()


__all__ = [
    "is_notebook",
    "merge_tif_directory",
    "merge_tif_files",
]
