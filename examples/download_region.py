# Copyright (c) kerem.ai. All Rights Reserved.

import argparse

import ee

from utils import OUTPUTS_DIR, run_example  # noqa: F401 isort: skip
from src import AlphaEarthDownloader  # noqa: F401 isort: skip


def parse_args() -> dict:
    parser = argparse.ArgumentParser("Download AlphaEarth embeddings for a country.")
    parser.add_argument("project", type=str, help="Google Cloud project ID.")
    parser.add_argument(
        "--country",
        type=str,
        default="Turkey",
        help="Name of the country to download embeddings for. (default: Turkey)",
    )  # --country Turkey
    parser.add_argument(
        "--year",
        type=int,
        default=2024,
        help="Year to download embeddings for. (default: 2024)",
    )  # --year 2024
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
    country: str,
    year: int,
    scale: int,
    dtype: str,
) -> None:
    # Initialize downloader
    downloader = AlphaEarthDownloader(project=project)

    # Get country geometry
    region = ee.FeatureCollection("FAO/GAUL/2015/level0").filter(
        ee.Filter.eq("ADM0_NAME", country)
    )
    geometry = region.geometry()

    # Download embeddings
    downloader.download_by_region(
        output_dir=OUTPUTS_DIR / country / str(year),
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        region=geometry,
        scale=scale,
        dtype=dtype,
        prefix="",
    )


if __name__ == "__main__":
    with run_example():
        main(**parse_args())
