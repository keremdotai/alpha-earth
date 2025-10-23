# Copyright (c) kerem.ai. All Rights Reserved.

from datetime import datetime

import ee
import geemap


class AlphaEarthDownloader:
    """
    Download AlphaEarth embeddings from Google Earth Engine.
    """

    DATASET_ID = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
    NUM_BANDS = 64
    BAND_NAMES = [f"A{i:02d}" for i in range(NUM_BANDS)]

    def __init__(self, project: str | None = None, authenticate: bool = True):
        """
        Initialize the downloader.

        Parameters
        ----------
        project:
            Google Cloud project ID (required for Earth Engine access)
        authenticate:
            Whether to authenticate with Earth Engine
        """
        if authenticate:
            try:
                # Try to initialize with project
                if project:
                    ee.Initialize(project=project)
                else:
                    # Try default initialization first
                    try:
                        ee.Initialize()
                    except Exception as e:
                        if (
                            "project" in str(e).lower()
                            or "not registered" in str(e).lower()
                        ):
                            raise ValueError(
                                "Earth Engine requires a project ID. Please provide your "
                                "Google Cloud project ID:\n"
                                "  downloader = AlphaEarthDownloader(project='your-project-id')\n"
                                "Or set the EE_PROJECT environment variable."
                            ) from e
                        raise
            except Exception as e:
                if "project" in str(e).lower() or "not registered" in str(e).lower():
                    raise
                print("Authentication required. Running ee.Authenticate()...")
                ee.Authenticate()
                if project:
                    ee.Initialize(project=project)
                else:
                    ee.Initialize()

        self.collection = ee.ImageCollection(self.DATASET_ID)

    def download_by_latlon(
        self,
        start_date: str,
        end_date: str,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        output_path: str,
        scale: int = 10,
        bands: list[str] | None = None,
    ) -> dict:
        """
        Download AlphaEarth embeddings for a lat/lon bounding box.

        Parameters
        ----------
        start_date:
            Start date in format 'YYYY-MM-DD'
        end_date:
            End date in format 'YYYY-MM-DD'
        min_lat:
            Minimum latitude (degrees, -90 to 90)
        max_lat:
            Maximum latitude (degrees, -90 to 90)
        min_lon:
            Minimum longitude (degrees, -180 to 180)
        max_lon:
            Maximum longitude (degrees, -180 to 180)
        output_path:
            Path to save the output file (GeoTIFF)
        scale:
            Spatial resolution in meters (default: 10m)
        bands:
            List of band names to download (default: all 64 bands)

        Returns
        -------
        dict:
            Dictionary with download information.
        """
        # Create bounding box geometry (WGS84)
        bbox = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

        return self._download(
            start_date=start_date,
            end_date=end_date,
            geometry=bbox,
            output_path=output_path,
            scale=scale,
            bands=bands,
            crs="EPSG:4326",
        )

    def download_by_utm(
        self,
        start_date: str,
        end_date: str,
        utm_zone: int,
        min_easting: float,
        max_easting: float,
        min_northing: float,
        max_northing: float,
        hemisphere: str = "N",
        output_path: str = None,
        scale: int = 10,
        bands: list[str] | None = None,
    ) -> dict:
        """
        Download AlphaEarth embeddings for a UTM coordinate range.
        UTM is the native coordinate system used by AlphaEarth (10m resolution).

        Parameters
        ----------
        start_date:
            Start date in format 'YYYY-MM-DD'
        end_date:
            End date in format 'YYYY-MM-DD'
        utm_zone:
            UTM zone number (1-60)
        min_easting:
            Minimum easting coordinate (meters)
        max_easting:
            Maximum easting coordinate (meters)
        min_northing:
            Minimum northing coordinate (meters)
        max_northing:
            Maximum northing coordinate (meters)
        hemisphere:
            'N' for northern, 'S' for southern hemisphere
        output_path:
            Path to save the output file (GeoTIFF)
        scale:
            Spatial resolution in meters (default: 10m)
        bands:
            List of band names to download (default: all 64 bands)

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

        return self._download(
            start_date=start_date,
            end_date=end_date,
            geometry=bbox,
            output_path=output_path,
            scale=scale,
            bands=bands,
            crs=epsg_code,
        )

    def _download(
        self,
        start_date: str,
        end_date: str,
        geometry: ee.Geometry,
        output_path: str,
        scale: int,
        bands: list[str] | None,
        crs: str,
    ) -> dict:
        """
        Internal method to download embeddings.

        Parameters
        ----------
        start_date:
            Start date in format 'YYYY-MM-DD'
        end_date:
            End date in format 'YYYY-MM-DD'
        geometry:
            Earth Engine geometry object
        output_path:
            Output file path
        scale:
            Resolution in meters
        bands:
            Band names to export
        crs:
            Coordinate reference system

        Returns
        -------
        dict:
            Dictionary with download information.
        """
        # Filter collection by date and location
        filtered = self.collection.filterDate(start_date, end_date).filterBounds(
            geometry
        )

        # Get image count
        count = filtered.size().getInfo()

        if count == 0:
            return {
                "status": "error",
                "message": "No images found for specified date range and location",
            }

        # Mosaic images if multiple years/tiles
        image = filtered.mosaic()

        # Select bands
        if bands is None:
            bands = self.BAND_NAMES
        image = image.select(bands)

        # Clip to geometry
        image = image.clip(geometry)

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

        # Download using geemap
        try:
            geemap.ee_export_image(
                image, filename=output_path, scale=scale, region=geometry, crs=crs
            )
            info["status"] = "success"
            info["output_path"] = output_path
        except Exception as e:
            info["status"] = "error"
            info["error"] = str(e)
            print(f"✗ Download failed: {e}")

        return info

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
