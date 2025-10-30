# Copyright (c) kerem.ai. All Rights Reserved.

from datetime import datetime
from pathlib import Path
from typing import Literal

import ee
import geemap
import numpy as np
from tqdm import tqdm

from .earthengine import EarthEngine
from .utils import quantize_ee


class AlphaEarthDownloader(EarthEngine):
    """
    Download AlphaEarth embeddings from Google Earth Engine.
    """

    DATASET_ID = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
    NUM_BANDS = 64
    BAND_NAMES = [f"A{i:02d}" for i in range(NUM_BANDS)]

    def __init__(self, project: str | None = None, authenticate: bool = True) -> None:
        """
        Initialize the downloader.

        Parameters
        ----------
        project:
            Google Cloud project ID (required for Earth Engine access).
        authenticate:
            Whether to authenticate with Earth Engine.
        """
        EarthEngine.__init__(self, project, authenticate)

        # Initialize the collection
        self.collection = ee.ImageCollection(self.DATASET_ID)

    def download_by_region(
        self,
        output_dir: str | Path | None,
        start_date: str,
        end_date: str,
        region: ee.FeatureCollection | ee.Geometry,
        scale: int = 10,
        bands: list[str] | None = None,
        dtype: Literal["uint8", "float32"] = "float32",
        prefix: str = "",
    ) -> ee.Image | dict:
        """
        Download AlphaEarth embeddings for a region.

        Parameters
        ----------
        output_dir:
            Path to save the output file/s (GeoTIFF).
            If None, an ee.Image object will be returned.
        start_date:
            Start date in format 'YYYY-MM-DD'.
        region:
            Region to download embeddings for.
        scale:
            Spatial resolution in meters (default: 10m).
        bands:
            List of band names to download (default: all 64 bands).
        dtype:
            Data type of the output file (default: uint8).
        prefix:
            Prefix to add to the output filename/s.

        Returns
        -------
        list[ee.Image | dict]:
            List of ee.Image objects if output_path is None,
            otherwise list of dictionaries with download information.
        """
        if isinstance(region, ee.FeatureCollection):
            geometry = region.geometry()
        else:
            geometry = region

        return self._download_image(
            output_dir=output_dir,
            start_date=start_date,
            end_date=end_date,
            geometry=geometry,
            scale=scale,
            bands=bands,
            crs="EPSG:4326",
            dtype=dtype,
            prefix=prefix,
        )

    def download_by_latlon(
        self,
        output_dir: str | Path | None,
        start_date: str,
        end_date: str,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        scale: int = 10,
        bands: list[str] | None = None,
        dtype: Literal["uint8", "float32"] = "float32",
    ) -> ee.Image | dict:
        """
        Download AlphaEarth embeddings for a lat/lon bounding box.

        Parameters
        ----------
        output_dir:
            Path to save the output file/s (GeoTIFF).
            If None, an ee.Image object will be returned.
        start_date:
            Start date in format 'YYYY-MM-DD'.
        end_date:
            End date in format 'YYYY-MM-DD'.
        min_lat:
            Minimum latitude (degrees, -90 to 90).
        max_lat:
            Maximum latitude (degrees, -90 to 90).
        min_lon:
            Minimum longitude (degrees, -180 to 180).
        max_lon:
            Maximum longitude (degrees, -180 to 180).
        scale:
            Spatial resolution in meters (default: 10m).
        bands:
            List of band names to download (default: all 64 bands).
        dtype:
            Data type of the output file (default: uint8).

        Returns
        -------
        ee.Image | dict:
            ee.Image object if output_path is None,
            otherwise dictionary with download information.
        """
        # Create bounding box geometry (WGS84)
        bbox = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

        return self._download_image(
            output_dir=output_dir,
            start_date=start_date,
            end_date=end_date,
            geometry=bbox,
            scale=scale,
            bands=bands,
            crs="EPSG:4326",
            dtype=dtype,
        )

    def download_by_utm(
        self,
        output_dir: str | Path | None,
        start_date: str,
        end_date: str,
        utm_zone: int,
        min_easting: float,
        max_easting: float,
        min_northing: float,
        max_northing: float,
        hemisphere: str = "N",
        scale: int = 10,
        bands: list[str] | None = None,
        dtype: Literal["uint8", "float32"] = "float32",
    ) -> dict:
        """
        Download AlphaEarth embeddings for a UTM coordinate range.
        UTM is the native coordinate system used by AlphaEarth (10m resolution).

        Parameters
        ----------
        output_dir:
            Path to save the output file/s (GeoTIFF).
            If None, an ee.Image object will be returned.
        start_date:
            Start date in format 'YYYY-MM-DD'.
        end_date:
            End date in format 'YYYY-MM-DD'.
        utm_zone:
            UTM zone number (1-60).
        min_easting:
            Minimum easting coordinate (meters).
        max_easting:
            Maximum easting coordinate (meters).
        min_northing:
            Minimum northing coordinate (meters).
        max_northing:
            Maximum northing coordinate (meters).
        hemisphere:
            'N' for northern, 'S' for southern hemisphere.
        scale:
            Spatial resolution in meters (default: 10m).
        bands:
            List of band names to download (default: all 64 bands).
        dtype:
            Data type of the output file (default: uint8).

        Returns
        -------
        dict:
            Dictionary with download information.
        """
        # Construct EPSG code for UTM zone
        # Northern hemisphere: 32600 + zone, Southern: 32700 + zone
        epsg_base = 32600 if hemisphere.upper() == "N" else 32700
        epsg_code = f"EPSG:{epsg_base + utm_zone}"

        # Create bounding box using Polygon instead of Rectangle for projected coordinates
        # Rectangle only works with geodesic projections
        bbox = ee.Geometry.Polygon(
            [
                [
                    [min_easting, min_northing],
                    [max_easting, min_northing],
                    [max_easting, max_northing],
                    [min_easting, max_northing],
                    [min_easting, min_northing],
                ]
            ],
            proj=epsg_code,
            geodesic=False,
        )

        return self._download_image(
            output_dir=output_dir,
            start_date=start_date,
            end_date=end_date,
            geometry=bbox,
            scale=scale,
            bands=bands,
            crs=epsg_code,
            dtype=dtype,
        )

    def _download_image(
        self,
        output_dir: str | Path | None,
        start_date: str,
        end_date: str,
        geometry: ee.Geometry,
        scale: int,
        bands: list[str] | None,
        crs: str,
        dtype: str,
        prefix: str = "",
    ) -> ee.Image | dict:
        """
        Internal method to download embeddings.

        Parameters
        ----------
        output_dir:
            Directory to save the output file/s (GeoTIFF).
            If None, an ee.Image object will be returned.
        start_date:
            Start date in format 'YYYY-MM-DD'.
        end_date:
            End date in format 'YYYY-MM-DD'.
        geometry:
            Earth Engine geometry object.
        scale:
            Resolution in meters.
        bands:
            Band names to export.
        crs:
            Coordinate reference system.
        dtype:
            Data type of the output file.
        prefix:
            Prefix to add to the output filename/s.

        Returns
        -------
        ee.Image | dict:
            Dictionary with download information.
        """
        # Filter collection by date and location
        filtered = self.collection.filterDate(start_date, end_date)
        filtered: ee.ImageCollection = filtered.filterBounds(geometry)

        # Get image count
        count = filtered.size().getInfo()
        if count == 0:
            raise ValueError("No images found for specified date range and location.")

        # Select bands
        if bands is None:
            bands = self.BAND_NAMES
        filtered = filtered.select(bands)

        # Return ee.Image object if output_dir is None
        if output_dir is None:
            return self._prepare_image(filtered.mosaic(), geometry, dtype)

        # Get image info
        # Use error margin for projected geometries (required for UTM)
        bounds = self._get_bounds(geometry)

        info = {
            "start_date": start_date,
            "end_date": end_date,
            "bounds": bounds,
            "bands": bands,
            "scale": scale,
            "crs": crs,
            "num_images": count,
            "files": [],
        }

        # Mkdir output directory
        output_dir.mkdir(mode=0o777, parents=True, exist_ok=True)
        assert output_dir.is_dir(), f"output_dir must be a directory: {output_dir}."

        pbar = tqdm(
            range(count), total=count, desc="Downloading images", colour="#00c8ff"
        )
        for i in pbar:
            # Get the image from the collection
            image = self._prepare_image(
                ee.Image(filtered.toList(count).get(i)), geometry, dtype
            )
            img_geometry = image.geometry()

            # Get the output path for the image
            filename = self._get_filename(self._get_bounds(img_geometry), dtype, prefix)
            path = output_dir / filename

            # Download the image from the generated url
            info["files"].append(
                self._download_from_url(image, scale, img_geometry, crs, path)
            )

        return info

    @classmethod
    def _prepare_image(
        cls, image: ee.Image, geometry: ee.Geometry, dtype: str
    ) -> ee.Image:
        """
        Prepare the given image for download.

        Parameter
        ---------
        image:
            Earth Engine image object.
        geometry:
            Earth Engine geometry object.
        dtype:
            Data type of the output file.

        Returns
        -------
        ee.Image:
            Earth Engine image object.
        """
        # Clip the image to the geometry
        image = image.clip(geometry)

        # Convert the image to the requested dtype
        image = cls._convert_dtype(image, dtype)

        return image

    @classmethod
    def _get_bounds(cls, geometry: ee.Geometry) -> dict:
        """
        Get the bounds of the given geometry.

        Parameters
        ----------
        geometry:
            Earth Engine geometry object.

        Returns
        -------
        dict:
            Dictionary with bounds information.
        """
        try:
            bounds = geometry.bounds(1).getInfo()  # 1 meter error margin
        except BaseException:
            bounds = geometry.bounds().getInfo()

        return bounds

    @classmethod
    def _get_filename(cls, bounds: dict, dtype: str, prefix: str) -> str:
        """
        Get the filename for the given bounds.

        Parameters
        ----------
        bounds:
            Dictionary with bounds information.
        dtype:
            Data type of the output file.
        prefix:
            Prefix to add to the output filename.

        Returns
        -------
        str:
            Filename.
        """
        filename = prefix + "_" if prefix else ""
        filename += f"{dtype}_"
        coords = np.array(bounds["coordinates"][0])
        max_lon, max_lat = np.max(coords, axis=0)
        min_lon, min_lat = np.min(coords, axis=0)
        filename += f"[{min_lat:.3f}|{max_lat:.3f}|{min_lon:.3f}|{max_lon:.3f}].tif"

        return filename

    @classmethod
    def _download_from_url(
        cls,
        image: ee.Image,
        scale: int,
        geometry: ee.Geometry,
        crs: str,
        output_path: Path,
    ) -> dict:
        """
        Internal method to download embeddings from a URL.

        Parameters
        ----------
        image:
            Earth Engine image object.
        scale:
            Resolution in meters.
        geometry:
            Earth Engine geometry object.
        crs:
            Coordinate reference system.
        output_path:
            Path to save the output file (GeoTIFF).

        Returns
        -------
        dict:
            Dictionary with download information.
        """
        try:
            # Export image to file
            geemap.ee_export_image(
                image,
                filename=output_path,
                scale=scale,
                region=geometry,
                crs=crs,
                verbose=False,
            )
            return {"success": True, "output_path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def _convert_dtype(cls, image: ee.Image, dtype: str) -> ee.Image:
        """
        Internal method to convert the image to the requested dtype.

        Parameters
        ----------
        image:
            Earth Engine image object.
        dtype:
            Data type of the output file.

        Returns
        -------
        ee.Image:
            Earth Engine image object with the requested dtype.
        """
        if dtype == "uint8":
            return quantize_ee(image)
        elif dtype == "float32":
            return image.float()
        else:
            raise ValueError(f"Invalid dtype: {dtype}")

    def get_available_dates(self, geometry: ee.Geometry | None = None) -> list[str]:
        """
        Get list of available dates in the collection.

        Parameters
        ----------
        geometry:
            Optional geometry to filter by location

        Returns
        -------
        list[str]:
            List of available dates.
        """
        collection = self.collection
        if geometry:
            collection = collection.filterBounds(geometry)

        dates = collection.aggregate_array("system:time_start").getInfo()
        return [datetime.fromtimestamp(d / 1000).strftime("%Y-%m-%d") for d in dates]

    def get_info(self) -> dict:
        """
        Get information about the AlphaEarth dataset.

        Returns
        -------
        dict:
            Dictionary with dataset information.
        """
        return {
            "dataset_id": self.DATASET_ID,
            "num_bands": self.NUM_BANDS,
            "band_names": self.BAND_NAMES,
            "resolution": "10m",
            "temporal_coverage": "2017-2024 (annual)",
            "coordinate_system": "UTM (native), WGS84 supported",
            "band_range": "-1 to 1 (unit vectors)",
            "license": "CC-BY 4.0",
        }
