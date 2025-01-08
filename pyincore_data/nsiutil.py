# Copyright (c) 2025 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
import geopandas as gpd

from pyincore_data.utils.datautil import DataUtil


class NSI:
    @staticmethod
    def create_nsi_gdf_by_county_fips(in_fips):
        """
        Creates a GeoDataFrame by NSI data for a county FIPS codes.

        Args:
            in_fips (Str): A county FIPS code (e.g., '29001').

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing data for provided FIPS codes.
        """
        # get feature collection from NIS api
        gdf = DataUtil.get_features_by_fips(in_fips)

        return gdf

    @staticmethod
    def create_nsi_gdf_by_counties_fips_list(fips_list):
        """
        Creates a merged GeoDataFrame by fetching and combining NSI data for a list of county FIPS codes.

        Args:
            fips_list (list): A list of county FIPS codes (e.g., ['15005', '29001']).

        Returns:
            gpd.GeoDataFrame: A merged GeoDataFrame containing data for all provided FIPS codes.
        """
        # initialize an empty GeoDataFrame
        merged_gdf = gpd.GeoDataFrame()

        for fips in fips_list:
            print(f"Processing FIPS: {fips}")
            gdf = DataUtil.get_features_by_fips(fips)

            if gdf is not None and not gdf.empty:
                merged_gdf = gpd.GeoDataFrame(pd.concat([merged_gdf, gdf], ignore_index=True))

        # ensure CRS consistency in the merged GeoDataFrame
        if not merged_gdf.empty:
            merged_gdf = merged_gdf.set_crs(epsg=4326)

        return merged_gdf
