# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/
import collections
import csv
import math
import os
import re
from typing import List, Dict
from collections import Counter

from decimal import getcontext, Decimal

from pyincore import DataService
from pyincore.globals import DAMAGE_PRECISION
from pyincore.utils import evaluateexpression


class DataUtil:

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
    def convert_dislocation_gpd_to_geopackage(in_gpd, programname, savefile):
        """Create shapefile of dislocation geodataframe.

        Args:
            in_gpd (object): Geodataframe of the dislocation.
            programname (str): Output directory name.
            savefile (str): Output shapefile name.

        """
        # save cen_shp_blockgroup_merged shapefile
        print('GeoPackage data file saved to: '+programname+'/'+savefile+".gpkg")
        in_gpd.to_file(programname+'/'+savefile+".gpkg", driver="GPKG")

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
