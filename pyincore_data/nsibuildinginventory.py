import os
import geopandas as gpd
from pyincore_data.nsiparser import NsiParser
from pyincore_data.utils.nsiutil import NsiUtil


class NsiBuildingInventory:
    @staticmethod
    def convert_nsi_to_building_inventory_by_county_fips_list(fips_list):
        """
        Convert NSI data to building inventory data by county FIPS list

        Contributors
        | Original Code and Logic: Dylan R. Sanderson
        | Implementation: Yong Wook Kim

        :param fips_list: list of county FIPS codes. The list should be string list not numeric
        :return: geodataframe with building inventory data
        """
        gdf = NsiParser.create_nsi_gdf_by_counties_fips_list(fips_list)
        region = NsiUtil.determine_region_by_fips(fips_list[0])
        gdf = NsiUtil.assign_hazus_specific_structure_type(gdf, region, False, random=False)
        gdf.set_index('guid', inplace=True)

        return gdf

    @staticmethod
    def convert_nsi_to_building_inventory_from_geojson(in_json, region="westCoast"):
        """
        Convert NSI data to building inventory data from GeoJSON file

        Contributors
        | Original Code and Logic: Dylan R. Sanderson
        | Implementation: Yong Wook Kim

        :param in_json:
        :param region: region of the data, it should be either eastCoast, westCoast, or midWest

        :return: geodataframe with building inventory data
        """
        gdf = gpd.read_file(in_json)
        gdf = NsiUtil.assign_hazus_specific_structure_type(gdf, region, False, random=False)
        gdf.set_index('guid', inplace=True)

        return gdf
