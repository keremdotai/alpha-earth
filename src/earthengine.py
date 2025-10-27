# Copyright (c) kerem.ai. All Rights Reserved.

import ee


class EarthEngine:
    """
    Earth Engine client for authentication and initialization.
    """

    def __init__(self, project: str | None = None, authenticate: bool = True) -> None:
        """
        Initialize the Earth Engine client.

        Parameters
        ----------
        project:
            Google Cloud project ID (required for Earth Engine access).
        authenticate:
            Whether to authenticate with Earth Engine.
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
