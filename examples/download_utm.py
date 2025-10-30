# Copyright (c) kerem.ai. All Rights Reserved.

import argparse

from utils import OUTPUTS_DIR, run_example  # noqa: F401 isort: skip
from src import AlphaEarthDownloader  # noqa: F401 isort: skip


def parse_args() -> dict:
    parser = argparse.ArgumentParser(
        "Download AlphaEarth embeddings for a UTM coordinate range."
    )
    parser.add_argument(
        "--project",
        type=str,
        default="keremdotai-2025",
        help="Google Cloud project ID.",
    )
    parser.add_argument(
        "--utm_zone", type=int, default=35, help="UTM zone number."
    )  # --utm_zone 35
    parser.add_argument(
        "--min_easting", type=float, default=517700, help="Minimum easting coordinate."
    )  # --min_easting 517700
    parser.add_argument(
        "--max_easting", type=float, default=562250, help="Maximum easting coordinate."
    )  # --max_easting 562250
    parser.add_argument(
        "--min_northing",
        type=float,
        default=4084500,
        help="Minimum northing coordinate.",
    )  # --min_northing 4084500
    parser.add_argument(
        "--max_northing",
        type=float,
        default=4117000,
        help="Maximum northing coordinate.",
    )  # --max_northing 4117000
    parser.add_argument(
        "--hemisphere", choices=["N", "S"], default="N", help="Hemisphere. (default: N)"
    )  # --hemisphere N
    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Year to download embeddings for. (default: 2024)",
    )  # --start_date 2020-01-01
    parser.add_argument(
        "--scale",
        type=int,
        default=1000,
        help="Spatial resolution in meters. (default: 1000)",
    )  # --scale 1000
    parser.add_argument(
        "--dtype",
        choices=["uint8", "float32"],
        default="float32",
        help="Data type of the output file. (default: float32)",
    )  # --dtype float32

    args = vars(parser.parse_args())

    # Validate arguments
    assert (args["year"] >= 2017) and (
        args["year"] <= 2024
    ), "Year must be between 2017 and 2024."
    assert args["scale"] >= 10, "Scale must be at least 10 meters."

    return args


def main(
    project: str,
    utm_zone: int,
    min_easting: float,
    max_easting: float,
    min_northing: float,
    max_northing: float,
    hemisphere: str,
    year: int,
    scale: int,
    dtype: str,
) -> None:
    # Initialize downloader
    downloader = AlphaEarthDownloader(project=project)

    # Download embeddings
    output_dir = (
        OUTPUTS_DIR
        / f"utm_{utm_zone}_{hemisphere}"
        / f"{min_easting}_{max_easting}_{min_northing}_{max_northing}"
        / str(year)
    )

    downloader.download_by_utm(
        output_dir=output_dir,
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        utm_zone=utm_zone,
        min_easting=min_easting,
        max_easting=max_easting,
        min_northing=min_northing,
        max_northing=max_northing,
        hemisphere=hemisphere,
        scale=scale,
        dtype=dtype,
    )


if __name__ == "__main__":
    with run_example():
        main(**parse_args())
