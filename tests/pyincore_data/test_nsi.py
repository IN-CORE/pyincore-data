# Copyright (c) 2025 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import pytest

from pyincore_data.nsiparser import NsiParser
from pyincore_data.utils.nsiutil import NsiUtil
from pyincore_data.nsibuildinginventory import NsiBuildingInventory


@pytest.fixture
def client():
    return pytest.client


def test_create_nsi_gdf_by_county_fips():
    fips = '15005'
    gdf = NsiParser.create_nsi_gdf_by_county_fips(fips)

    assert gdf.shape[0] > 0


def test_create_nsi_gdf_by_counties_fips_list():
    fips_list = ['15005', '29001', '01001']
    merged_gdf = NsiParser.create_nsi_gdf_by_counties_fips_list(fips_list)

    assert merged_gdf.shape[0] > 0


def test_get_county_fips_by_state():
    state = 'illinois'
    fips_list = NsiParser.get_county_fips_by_state(state)

    assert len(fips_list) > 0


def test_get_county_fips_only_list_by_state():
    state = 'illinois'
    fips_list = NsiParser.get_county_fips_only_list_by_state(state)

    assert len(fips_list) > 0


def test_get_fips_by_state_and_county():
    state = 'illinois'
    county = 'champaign'
    fips = NsiParser.get_fips_by_state_and_county(state, county)

    assert fips == '17019'


def test_create_building_inventory_by_county_fips_list():
    fips_list = ['36021']   # new york county
    gdf = NsiBuildingInventory.convert_nsi_to_building_inventory_by_county_fips_list(fips_list)
    assert gdf['struct_typ'].notna().all(), "struct_typ contains NaN values"
    assert gdf['dgn_lvl'].notna().all(), "dgn_lvl contains NaN values"


def test_create_building_inventory_by_geojson():
    in_json = 'test1.json'
    gdf = NsiBuildingInventory.convert_nsi_to_building_inventory_from_geojson(in_json, "westCoast")
    assert gdf['struct_typ'].notna().all(), "struct_typ contains NaN values"
    assert gdf['dgn_lvl'].notna().all(), "dgn_lvl contains NaN values"


def test_define_region_by_fips():
    fips = '15005'
    region = NsiUtil.determine_region_by_fips(fips)
    valid_regions = {"WestCoast", "MidWest", "EastCoast", "Unknown"}
    assert region in valid_regions, f"Unexpected region returned: {region}"

