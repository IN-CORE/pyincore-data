import os
import geopandas as gpd
from pyincore_data.nsiparser import NsiParser
from pyincore_data.utils.nsiutil import NsiUtil


class NsiBuildingInventory:
    @staticmethod
    def convert_nsi_to_building_inventory_by_county_fips_list(fips_list):
        """
        Convert NSI data to building inventory data by county FIPS list

        :param fips_list: list of county FIPS codes
        :return: geodataframe with building inventory data
        """
        gdf = NsiParser.create_nsi_gdf_by_counties_fips_list(fips_list)
        gdf = NsiUtil.assign_hazus_specific_structure_type(gdf, False, random=False)
        gdf.set_index('guid', inplace=True)

        return gdf

    @staticmethod
    def convert_nsi_to_building_inventory_from_geojson(in_json):
        """
        Convert NSI data to building inventory data from GeoJSON file

        :param in_json:
        :return: geodataframe with building inventory data
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        in_json = os.path.join(script_dir, 'nsi-seaside.json')
        gdf = gpd.read_file(in_json)
        gdf = NsiUtil.assign_hazus_specific_structure_type(gdf, False, random=False)
        gdf.set_index('guid', inplace=True)

        return gdf
