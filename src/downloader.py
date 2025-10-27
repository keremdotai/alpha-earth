# Copyright (c) kerem.ai. All Rights Reserved.

from datetime import datetime
from pathlib import Path
from typing import Literal

import ee
import geemap

from .earthengine import EarthEngine


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
        output_path: str | Path | None,
        start_date: str,
        end_date: str,
        region: ee.FeatureCollection | ee.Geometry,
        scale: int = 10,
        bands: list[str] | None = None,
        dtype: Literal["uint8", "uint16", "float32", "float64"] = "float32",
    ) -> ee.Image | dict:
        """
        Download AlphaEarth embeddings for a region.

        Parameters
        ----------
        output_path:
            Path to save the output file (GeoTIFF).
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
            output_path=output_path,
            start_date=start_date,
            end_date=end_date,
            geometry=geometry,
            scale=scale,
            bands=bands,
            crs="EPSG:4326",
            dtype=dtype,
        )

    def download_by_latlon(
        self,
        output_path: str | Path | None,
        start_date: str,
        end_date: str,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        scale: int = 10,
        bands: list[str] | None = None,
        dtype: Literal["uint8", "uint16", "float32", "float64"] = "float32",
    ) -> ee.Image | dict:
        """
        Download AlphaEarth embeddings for a lat/lon bounding box.

        Parameters
        ----------
        output_path:
            Path to save the output file (GeoTIFF).
            If None, the image will be returned as an ee.Image object.
            Otherwise, the image will be saved to the specified path.
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
            output_path=output_path,
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
        output_path: str,
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
        dtype: Literal["uint8", "uint16", "float32", "float64"] = "float32",
    ) -> dict:
        """
        Download AlphaEarth embeddings for a UTM coordinate range.
        UTM is the native coordinate system used by AlphaEarth (10m resolution).

        Parameters
        ----------
        output_path:
            Path to save the output file (GeoTIFF).
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
            output_path=output_path,
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
        output_path: str | Path | None,
        start_date: str,
        end_date: str,
        geometry: ee.Geometry,
        scale: int,
        bands: list[str] | None,
        crs: str,
        dtype: Literal["uint8", "uint16", "float32", "float64"],
    ) -> ee.Image | dict:
        """
        Internal method to download embeddings.

        Parameters
        ----------
        output_path:
            Path to save the output file (GeoTIFF).
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

        Returns
        -------
        ee.Image | dict:
            Dictionary with download information.
        """
        # Filter collection by date and location
        filtered = self.collection.filterDate(start_date, end_date).filterBounds(
            geometry
        )

        # Get image count
        count = filtered.size().getInfo()

        if count == 0:
            raise ValueError("No images found for specified date range and location.")

        # Mosaic images if multiple years/tiles
        image = filtered.mosaic()

        # Select bands
        if bands is None:
            bands = self.BAND_NAMES
        image = image.select(bands)

        # Clip to geometry
        image = image.clip(geometry)

        # Convert to requested dtype
        image = self._convert_dtype(image, dtype)

        # Return image if no output path is provided
        if output_path is None:
            return image
        output_path = Path(output_path)

        # Get image info
        # Use error margin for projected geometries (required for UTM)
        try:
            bounds = geometry.bounds(1).getInfo()  # 1 meter error margin
        except BaseException:
            bounds = geometry.bounds().getInfo()

        info = {
            "start_date": start_date,
            "end_date": end_date,
            "bounds": bounds,
            "bands": bands,
            "scale": scale,
            "crs": crs,
            "num_images": count,
        }

        # Download image from URL
        info.update(self._download_from_url(image, scale, geometry, crs, output_path))

        return info

    @classmethod
    def _download_from_url(
        cls,
        image: ee.Image | ee.ImageCollection,
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
        is_collection = isinstance(image, ee.ImageCollection)
        if is_collection:
            assert (
                output_path.exists() and output_path.is_dir()
            ), "Output path must be a directory if downloading an image collection."

        try:
            if is_collection:
                # Export image collection to directory
                geemap.ee_export_image_collection(
                    image, out_dir=output_path, scale=scale, region=geometry, crs=crs
                )
            else:
                # Export image to file
                geemap.ee_export_image(
                    image, filename=output_path, scale=scale, region=geometry, crs=crs
                )
            return {"success": True, "output_path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def _convert_dtype(
        cls,
        image: ee.Image | ee.ImageCollection,
        dtype: Literal["uint8", "uint16", "float32", "float64"],
    ) -> ee.Image | ee.ImageCollection:
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
            return image.add(1).divide(2).multiply(255).clamp(0, 255).uint8()
        elif dtype == "uint16":
            return image.add(1).divide(2).multiply(65535).clamp(0, 65535).uint16()
        elif dtype == "float32":
            return image.float()
        elif dtype == "float64":
            return image
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
