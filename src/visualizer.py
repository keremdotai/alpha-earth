# Copyright (c) kerem.ai. All Rights Reserved.

from pathlib import Path
from typing import Callable, Literal

import ee
import geemap
import geopandas as gpd
import rasterio

from .earthengine import EarthEngine
from .utils import is_notebook


class EarthEngineVisualizer(EarthEngine):
    """
    Visualizer for Earth Engine objects and GeoTIFF files.
    """

    def __init__(
        self,
        project: str | None = None,
        authenticate: bool = True,
        basemap: Literal["HYBRID", "SATELLITE", "ROADMAP", "TERRAIN"] = "HYBRID",
    ) -> None:
        """
        Initialize the visualizer.

        Parameters
        ----------
        project:
            Google Cloud project ID (required for Earth Engine access).
        authenticate:
            Whether to authenticate with Earth Engine.
        basemap:
            Basemap to use for the map.
        """
        EarthEngine.__init__(self, project, authenticate)

        # Initialize the map
        self.basemap = basemap
        self.reset()

    def reset(self) -> None:
        """
        Reset the map to the default state.
        """
        self.map: geemap.Map = geemap.Map()
        self.map.add_basemap(self.basemap)

    def plot_ee(
        self,
        obj: ee.Collection | ee.Feature | ee.Image,
        name: str,
        params: dict = {},
        opacity: float = 1.0,
    ) -> None:
        """
        Plot an Earth Engine object on the map.

        Parameters
        ----------
        obj:
            Earth Engine object to plot.
        name:
            Name of the layer.
        params:
            Parameters to pass to the layer.
        opacity:
            Opacity of the layer.
        """
        self.map.add_layer(obj, params, name, opacity=opacity)

    def plot_tif(
        self,
        path: str | Path,
        name: str,
        bands: list[int] | None = None,
        colormap: str | None = "viridis",
        vmin: float | None = None,
        vmax: float | None = None,
        params: dict = {},
        opacity: float = 1.0,
    ) -> None:
        """
        Plot a GeoTIFF file on the map.

        Parameters
        ----------
        path:
            Path to the GeoTIFF file.
        name:
            Name of the layer.
        bands:
            Bands to plot.
        colormap:
            Colormap to use.
        vmin:
            Minimum value to clip the data to.
        vmax:
            Maximum value to clip the data to.
        opacity:
            Opacity of the layer.
        """
        with rasterio.open(path, "r") as src:
            nodata = src.nodata
            count = src.count

        bands = bands or list(range(count))
        assert (
            len(bands) == 1 or len(bands) == 3
        ), f"Number of bands must be either 1 or 3. Got {len(bands)}."
        colormap = colormap if len(bands) == 1 else None

        self.map.add_raster(
            path,
            layer_name=name,
            indices=bands,
            colormap=colormap,
            vmin=vmin,
            vmax=vmax,
            nodata=nodata,
            vis_params=params,
            opacity=opacity,
        )

    def plot_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        name: str,
        style: dict = {},
        hover_style: dict = {},
        style_callback: Callable = None,
        fill_colors: list[str] = ["black"],
        opacity: float = 1.0,
    ) -> None:
        """
        Plot a GeoDataFrame on the map.

        Parameters
        ----------
        gdf:
            GeoDataFrame to plot.
        name:
            Name of the layer.
        style:
            Style to use for the layer.
        hover_style:
            Style to use for the hover layer.
        style_callback:
            Callback to use for the style.
        fill_colors:
            Colors to use for the fill.
        opacity:
            Opacity of the layer.
        """
        self.map.add_gdf(
            gdf,
            layer_name=name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            opacity=opacity,
        )

    def plot_geojson(
        self,
        geojson: dict,
        name: str,
        style: dict = {},
        hover_style: dict = {},
        style_callback: Callable = None,
        fill_colors: list[str] = ["black"],
        opacity: float = 1.0,
    ) -> None:
        """
        Plot a GeoJSON file on the map.

        Parameters
        ----------
        geojson:
            GeoJSON to plot.
        name:
            Name of the layer.
        style:
            Style to use for the layer.
        hover_style:
            Style to use for the hover layer.
        style_callback:
            Callback to use for the style.
        fill_colors:
            Colors to use for the fill.
        opacity:
            Opacity of the layer.
        """
        self.map.add_geojson(
            geojson,
            layer_name=name,
            style=style,
            hover_style=hover_style,
            style_callback=style_callback,
            fill_colors=fill_colors,
            opacity=opacity,
        )

    def set_center(
        self,
        obj: ee.Element | ee.Geometry | None = None,
        lat: float | None = None,
        lon: float | None = None,
        zoom: int | None = None,
    ) -> None:
        """
        Set the center of the map.
        Either obj or lat/lon must be provided.

        Parameters
        ----------
        obj:
            Object to center the map on.
        lat:
            Latitude of the center.
        lon:
            Longitude of the center.
        zoom:
            Zoom level of the map.
        """
        assert (obj is not None) or (
            lat is not None and lon is not None
        ), "Either obj or lat/lon must be provided."
        assert (zoom >= 0) and (zoom <= 24), "Zoom level must be between 0 and 24."

        if obj is not None:
            self.map.center_object(obj, zoom=zoom)
        else:
            self.map.set_center(lat, lon, zoom)

    def add_layer_control(self) -> None:
        """
        Add a layer control to the map.
        """
        self.map.add_layer_control()

    def add_legend(self, title: str, legend_dict: dict | None = None) -> None:
        """
        Add a legend to the map.
        """
        self.map.add_legend(title, legend_dict)

    def show(self) -> None:
        """
        Display the map in the notebook or in the browser.
        If the map cannot be displayed in inline mode, it will be displayed in browser.
        """
        if is_notebook():
            from IPython.display import display  # fmt: skip
            display(self.map)
        else:
            self.map.show_in_browser()

    def to_html(self, path: str | Path) -> None:
        """
        Save the map to an HTML file.

        Parameters
        ----------
        path:
            Path to save the HTML file (must end with .html).
        """
        path: Path = Path(path)
        assert path.suffix == ".html", "Path must end with .html."
        print(f"Saving map to {path}...")
        self.map.to_html(path)
