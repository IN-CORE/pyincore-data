# Copyright (c) 2025 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pandas as pd
import geopandas as gpd
import requests

from pyincore_data.utils.datautil import DataUtil
from pyincore_data import globals as pyincore_globals

# Static mapping of state names to FIPS codes (since the API doesn't directly return them in this case)
STATE_FIPS_CODES = pyincore_globals.STATE_FIPS_CODES


class NsiParser:
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

    @staticmethod
    def get_county_fips_by_state(state_name):
        """
        Fetches all county FIPS codes for a given state using the US Census Bureau API.

        Args:
            state_name (str): Full state name (e.g., "Illinois").

        Returns:
            list: A list of dictionaries containing county names and their FIPS codes.
        """
        # Normalize state name to title case for matching
        state_name_normalized = state_name.title()

        # Validate the state name and get the state FIPS code
        state_fips = STATE_FIPS_CODES.get(state_name_normalized)
        if not state_fips:
            raise ValueError(f"State '{state_name}' not found. Please check the spelling.")

        # Census API URL for county-level data
        county_fips_url = f"{pyincore_globals.COUNTY_FIPS_BASE_URL}?get=NAME&for=county:*&in=state:{state_fips}"
        response = requests.get(county_fips_url)

        if response.status_code != 200:
            raise ValueError(f"Error fetching counties for state '{state_name}': {response.status_code}")

        try:
            counties_data = response.json()
        except ValueError:
            raise ValueError("Failed to parse JSON response for counties.")

        # Ensure counties_data is valid
        if not isinstance(counties_data, list) or len(counties_data) < 2:
            raise ValueError("Unexpected data format for county FIPS codes.")

        # Extract county names and FIPS codes
        county_list = [
            {"county": row[0], "fips": f"{state_fips}{row[2]}"}
            for row in counties_data[1:]  # Skip the header
        ]

        return county_list

    @staticmethod
    def get_county_fips_only_list_by_state(state_name):
        """
        Fetches a list of FIPS codes for all counties in a given state.

        Args:
            state_name (str): Full state name (e.g., "Illinois").

        Returns:
            list: A list of FIPS codes (strings) for all counties in the state.
        """
        try:
            counties = NsiParser.get_county_fips_by_state(state_name)
            fips_list = [county['fips'] for county in counties]
            return fips_list
        except ValueError as e:
            print("Error:", e)
            return []

    @staticmethod
    def get_fips_by_state_and_county(state_name, county_name):
        """
        Fetches the FIPS code for a specific county in a given state.

        Args:
            state_name (str): Full state name (e.g., "Illinois").
            county_name (str): Full county name (e.g., "Champaign").

        Returns:
            str: The FIPS code for the specified county.
            None: If the state or county is not found.
        """
        try:
            # fetch all counties and their FIPS codes for the state
            counties = NsiParser.get_county_fips_by_state(state_name)

            # find the county by name
            for county in counties:
                county_name_cleaned = county['county'].split(',')[0].replace(" County", "").strip().lower()
                if county_name_cleaned == county_name.lower():
                    return county['fips']

            # if no match is found
            print(f"County '{county_name}' not found in state '{state_name}'.")
            return None
        except ValueError as e:
            print("Error:", e)
            return None
