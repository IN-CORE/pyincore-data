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

logger = globals.LOGGER

class CensusViz():
    """Utility methods for Census data and visualization"""

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
        # check the minimum value to use it to nan value, since nan value makes an error.
        min_val = pd[key].min()
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
