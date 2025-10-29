# Copyright (c) kerem.ai. All Rights Reserved.

import argparse

from utils import OUTPUTS_DIR, run_example  # noqa: F401 isort: skip
from src import AlphaEarthDownloader  # noqa: F401 isort: skip


def parse_args() -> dict:
    parser = argparse.ArgumentParser(
        "Download AlphaEarth embeddings for a UTM coordinate range."
    )
    parser.add_argument("project", type=str, help="Google Cloud project ID.")
    parser.add_argument(
        "--min_lat", type=float, default=36.7, help="Minimum latitude."
    )  # --min_lat 36.7
    parser.add_argument(
        "--max_lat", type=float, default=39.3, help="Maximum latitude."
    )  # --max_lat 39.3
    parser.add_argument(
        "--min_lon", type=float, default=31.2, help="Minimum longitude."
    )  # --min_lon 31.2
    parser.add_argument(
        "--max_lon", type=float, default=37.35, help="Maximum longitude."
    )  # --max_lon 37.35
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
        choices=["uint8", "uint16", "float32", "float64"],
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
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    year: int,
    scale: int,
    dtype: str,
) -> None:
    # Initialize downloader
    downloader = AlphaEarthDownloader(project=project)

    # Download embeddings
    output_dir = OUTPUTS_DIR / f"{min_lat}_{max_lat}_{min_lon}_{max_lon}" / str(year)

    downloader.download_by_latlon(
        output_dir=output_dir,
        start_date=f"{year}-01-01",
        end_date=f"{year + 1}-01-31",
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
        scale=scale,
        dtype=dtype,
    )


if __name__ == "__main__":
    with run_example():
        main(**parse_args())
