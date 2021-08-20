# Copyright (c) 2021 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import json
from math import isnan

import requests
import os
import pandas as pd
import geopandas as gpd
import folium as fm
import urllib.request
import shutil
import ipyleaflet as ipylft

from ipyleaflet import projections
from branca.colormap import linear
from pyincore_data import globals
from zipfile import ZipFile


class CensusUtil():
    """Utility methods for Geospatial Visualization"""

    @staticmethod
    def get_blockgroupdata_for_dislocation(state_counties: list, vintage: str = "2010", dataset_name: str = 'dec/sf1',
                                           out_csv: bool = False, out_shapefile: bool = False, out_html: bool = False,
                                           geo_name: str = "geo_name", program_name: str = "program_name"):

        """Create Geopandas DataFrame for population dislocation analysis from census dataset.

        Args:
            state_counties (list): A List of concatenated State and County FIPS Codes.
                see full list https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/home/?cid=nrcs143_013697
            vintage (str): Census Year.
            dataset_name (str): Census dataset name.
            out_csv (bool): Save output dataframe as csv.
            out_shapefile (bool): Save processed census geodataframe as shapefile.
            out_html (bool): Save processed folium map to html.
            geo_name (str): Name of geo area - used for naming output files.
            program_name (str): Name of directory used to save output files.

        Returns:
            obj, dict: A dataframe for dislocation analysis, and
            a dictionary containing geodataframe and folium map

        """

        logger = globals.LOGGER

        # ### Base API URL parameters, found at https://api.census.gov/data.html

        # Variable parameters
        get_vars = 'GEO_ID,NAME,P005001,P005003,P005004,P005010'
        # List variables to convert from dtype object to integer
        int_vars = ['P005001', 'P005003', 'P005004', 'P005010']
        # GEO_ID  = Geographic ID
        # NAME    = Geographic Area Name
        # P005001 = Total
        # P005003 = Total!!Not Hispanic or Latino!!White alone
        # P005004 = Total!!Not Hispanic or Latino!!Black or African American alone
        # P005010 = Total!!Hispanic or Latino

        # Make directory to save output
        if not os.path.exists(program_name):
            os.mkdir(program_name)

        # Make a directory to save downloaded shapefiles - folder will be made then deleted
        shapefile_dir = 'shapefiletemp'
        if not os.path.exists(shapefile_dir):
            os.mkdir(shapefile_dir)

        # loop through counties
        appended_countydata = []  # start an empty container for the county data
        for state_county in state_counties:
            # deconcatenate state and county values
            state = state_county[0:2]
            county = state_county[2:5]
            logger.debug('State:  '+state)
            logger.debug('County: '+county)

        # Set up hyperlink for Census API
        api_hyperlink = ('https://api.census.gov/data/' + vintage + '/'+dataset_name + '?get=' + get_vars +
                         '&in=state:' + state + '&in=county:' + county + '&for=block%20group:*')

        print("Census API data from: " + api_hyperlink)

        # Obtain Census API JSON Data
        apijson = requests.get(api_hyperlink)

        if apijson.status_code != 200:
            error_msg = "Failed to download the data from Census API."
            logger.error(error_msg)
            raise Exception(error_msg)

        # Convert the requested json into pandas dataframe
        apidf = pd.DataFrame(columns=apijson.json()[0], data=apijson.json()[1:])

        # Append county data makes it possible to have multiple counties
        appended_countydata.append(apidf)

        # Create dataframe from appended county data
        cen_blockgroup = pd.concat(appended_countydata)

        # Add variable named "Survey" that identifies Census survey program and survey year
        cen_blockgroup['Survey'] = vintage+' '+dataset_name

        # Set block group FIPS code by concatenating state, county, tract and block group fips
        cen_blockgroup['bgid'] = (cen_blockgroup['state']+cen_blockgroup['county'] +
                                  cen_blockgroup['tract']+cen_blockgroup['block group'])

        # To avoid problems with how the block group id is read saving it
        # as a string will reduce possibility for future errors
        cen_blockgroup['bgidstr'] = cen_blockgroup['bgid'].apply(lambda x: "BG"+str(x).zfill(12))

        # Convert variables from dtype object to integer
        for var in int_vars:
            cen_blockgroup[var] = cen_blockgroup[var].astype(int)
            print(var+' converted from object to integer')

        # Generate new variables
        cen_blockgroup['pwhitebg'] = cen_blockgroup['P005003'] / cen_blockgroup['P005001'] * 100
        cen_blockgroup['pblackbg'] = cen_blockgroup['P005004'] / cen_blockgroup['P005001'] * 100
        cen_blockgroup['phispbg'] = cen_blockgroup['P005010'] / cen_blockgroup['P005001'] * 100

        # ### Obtain Data - Download and extract shapefiles
        # The Block Group IDs in the Census data are associated with the Block Group boundaries that can be mapped.
        # To map this data, we need the shapefile information for the block groups in the select counties.
        #
        # These files can be found online at:
        # https://www2.census.gov/geo/tiger/TIGER2010/BG/2010/

        # ### Download and extract shapefiles
        # Block group shapefiles are downloaded for each of the selected counties from
        # the Census TIGER/Line Shapefiles at https://www2.census.gov/geo/tiger.
        # Each counties file is downloaded as a zipfile and the contents are extracted.
        # The shapefiles are reprojected to EPSG 4326 and appended as a single shapefile
        # (as a GeoPandas GeoDataFrame) containing block groups for all of the selected counties.
        #
        # *EPSG: 4326 uses a coordinate system (Lat, Lon)
        # This coordinate system is required for mapping with folium.

        # loop through counties
        appended_countyshp = []  # start an empty container for the county shapefiles
        for state_county in state_counties:

            # county_fips = state+county
            filename = f'tl_2010_{state_county}_bg10'

            # Use wget to download the TIGER Shapefile for a county
            # options -quiet = turn off wget output
            # add directory prefix to save files to folder named after program name
            shapefile_url = 'https://www2.census.gov/geo/tiger/TIGER2010/BG/2010/' + filename + '.zip'
            print(('Downloading Shapefiles for State_County: '
                   + state_county + ' from: '+shapefile_url).format(filename=filename))

            zip_file = os.path.join(shapefile_dir, filename + '.zip')
            urllib.request.urlretrieve(shapefile_url, zip_file)

            with ZipFile(zip_file, 'r') as zip_obj:
                zip_obj.extractall(path="shapefiletemp")
            # Read shapefile to GeoDataFrame
            gdf = gpd.read_file(f'shapefiletemp/{filename}.shp')

            # Set projection to EPSG 4326, which is required for folium
            gdf = gdf.to_crs(epsg=4326)

            # Append county data
            appended_countyshp.append(gdf)

        # Create dataframe from appended county data
        shp_blockgroup = pd.concat(appended_countyshp)

        # Clean Data - Merge Census demographic data to the appended shapefiles
        cen_shp_blockgroup_merged = pd.merge(shp_blockgroup, cen_blockgroup,
                                             left_on='GEOID10', right_on='bgid', how='left')

        # Set paramaters for file save
        save_columns = ['bgid', 'bgidstr', 'Survey', 'pblackbg', 'phispbg']  # set column names to save

        # ### Explore Data - Map merged block group shapefile and Census data

        bgmap = CensusUtil.create_dislocation_ipyleaflet_map_from_gpd(cen_shp_blockgroup_merged)

        savefile = program_name + '_' + geo_name  # set file name

        if out_html:
            folium_map = CensusUtil.create_dislocation_folium_map_from_gpd(cen_shp_blockgroup_merged)
            CensusUtil.save_dislocation_map_to_html(folium_map['map'], program_name, savefile)

        if out_csv:
            CensusUtil.convert_dislocation_pd_to_csv(cen_blockgroup, save_columns, program_name, savefile)

        if out_shapefile:
            CensusUtil.convert_dislocation_gpd_to_shapefile(cen_shp_blockgroup_merged, program_name, savefile)

        # clean up shapefile temp directory
        # Try to remove tree; if failed show an error using try...except on screen
        try:
            shutil.rmtree(shapefile_dir)
            if not out_shapefile and not out_csv and not out_html:
                shutil.rmtree(program_name)
        except OSError as e:
            error_msg = "Error: Failed to remove either " + shapefile_dir \
                        + " or " + program_name + " directory"
            logger.debug(error_msg)
            raise Exception(error_msg)

        return cen_blockgroup[save_columns], bgmap

    @staticmethod
    def convert_dislocation_gpd_to_shapefile(in_gpd, programname, savefile):
        """Create shapefile of dislocation geodataframe.

        Args:
            in_gpd (object): Geodataframe of the dislocation.
            programname (str): Output directory name.
            savefile (str): Output shapefile name.

        """
        # save cen_shp_blockgroup_merged shapefile
        print('Shapefile data file saved to: '+programname+'/'+savefile+".shp")
        in_gpd.to_file(programname+'/'+savefile+".shp")

    @staticmethod
    def convert_dislocation_pd_to_csv(in_pd, save_columns, programname, savefile):
        """Create csv of dislocation dataframe using the column names.

        Args:
            in_pd (object): Geodataframe of the dislocation.
            save_columns (list): A list of column names to use.
            programname (str): Output directory name.
            savefile (str): Output csv file name.

        """

        # Save cen_blockgroup dataframe with save_column variables to csv named savefile
        print('CSV data file saved to: '+programname+'/'+savefile+".csv")
        in_pd[save_columns].to_csv(programname+'/'+savefile+".csv", index=False)


    @staticmethod
    def create_dislocation_ipyleaflet_map_from_gpd(in_gpd, zoom_level=10):
        """Create ipyleaflet dislocation map for geodataframe.

        Args:
            in_gpd (object): Geodataframe of the dislocation.

        Returns:
            obj : An ipyleaflet map for dislocation

        """
        # What location should the map be centered on?
        center_x = in_gpd.bounds.minx.mean()
        center_y = in_gpd.bounds.miny.mean()

        out_map = ipylft.Map(center=(center_y, center_x), zoom=zoom_level,
                         crs=projections.EPSG3857, scroll_wheel_zoom=True)

        in_gpd_tmp = in_gpd[['GEOID10', 'phispbg', 'pblackbg', 'geometry']]
        geo_data_dic = json.loads(in_gpd_tmp.to_json())
        hisp_choro_data = CensusUtil.create_choro_data_from_pd(in_gpd, 'phispbg')
        black_choro_data = CensusUtil.create_choro_data_from_pd(in_gpd, 'pblackbg')

        # Add Percent Hispanic to Map
        layer1 = ipylft.Choropleth(
            geo_data=geo_data_dic,
            choro_data=hisp_choro_data,
            colormap=linear.YlOrRd_04,
            border_color='black',
            style={'fillOpacity': 0.8},
            name='phispbg'
        )

        # Add Percent Black to Map
        layer2 = ipylft.Choropleth(
            geo_data=geo_data_dic,
            choro_data=black_choro_data,
            colormap=linear.YlOrRd_04,
            border_color='black',
            style={'fillOpacity': 0.8},
            name='pblackbg'
        )

        out_map.add_layer(layer1)
        out_map.add_layer(layer2)

        out_map.add_control(ipylft.LayersControl(position='topright'))
        out_map.add_control(ipylft.FullScreenControl(position='topright'))

        # return geodataframe and map
        bgmap = {}  # start an empty dictionary
        bgmap['gdf'] = in_gpd.copy()
        bgmap['map'] = out_map

        return bgmap

    @staticmethod
    def create_choro_data_from_pd(pd, key):
        """Create choropleth's choro-data from dataframe.

        Args:
            pd (object): an Input dataframe.
            key (str): a string for dictionary key
        Returns:
            obj : A dictionary of dataframe

        """
        temp_id = list(range(len(pd[key])))
        temp_id = [str(i) for i in temp_id]
        choro_data = dict(zip(temp_id, pd[key]))
        for item in choro_data:
            if isnan(choro_data[item]):
                choro_data[item] = 0

        return choro_data

    @staticmethod
    def create_dislocation_folium_map_from_gpd(in_gpd):
        """Create folium dislocation map for geodataframe.

        Args:
            in_gpd (object): Geodataframe of the dislocation.

        Returns:
            obj : A folium map for dislocation

        """
        # What location should the map be centered on?
        center_x = in_gpd.bounds.minx.mean()
        center_y = in_gpd.bounds.miny.mean()

        out_folium_map = fm.Map(location=[center_y, center_x], zoom_start=10)

        # Add Percent Hispanic to Map
        fm.Choropleth(
            geo_data=in_gpd,
            data=in_gpd,
            columns=['GEOID10', 'phispbg'],
            key_on='feature.properties.GEOID10',
            fill_color='YlGnBu',
            name='Percent Hispanic',
            legend_name='Percent Hispanic (%)'
        ).add_to(out_folium_map)

        # Add Percent Black to Map
        fm.Choropleth(
            geo_data=in_gpd,
            data=in_gpd,
            columns=['GEOID10', 'pblackbg'],
            key_on='feature.properties.GEOID10',
            fill_color='YlGnBu',
            name='Percent Black',
            legend_name='Percent Black (%)'
        ).add_to(out_folium_map)

        fm.LayerControl().add_to(out_folium_map)

        # return geodataframe and map
        bgmap = {}  # start an empty dictionary
        bgmap['gdf'] = in_gpd.copy()
        bgmap['map'] = out_folium_map

        return bgmap

    @staticmethod
    def save_dislocation_map_to_html(folium_map, programname, savefile):
        """Save folium dislocation map to html.

        Args:
            in_gpd (object): Geodataframe of the dislocation.

        Returns:
            obj : An ipyleaflet map for dislocation
        """

        # save html map
        map_save_file = programname+'/'+savefile+'_map.html'
        print('Dynamic HTML map saved to: '+map_save_file)
        folium_map.save(map_save_file)
