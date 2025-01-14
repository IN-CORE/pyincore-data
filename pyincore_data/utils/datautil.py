# Copyright (c) 2022 University of Illinois and others. All rights reserved.
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

import fiona
import requests
import uuid
import os
import geopandas as gpd
import sqlalchemy

from sqlalchemy import create_engine
from geojson import FeatureCollection
from pyincore_data.config import Config


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
        print("Shapefile data file saved to: " + programname + "/" + savefile + ".shp")
        in_gpd.to_file(programname + "/" + savefile + ".shp")

    @staticmethod
    def convert_dislocation_gpd_to_geopackage(in_gpd, programname, savefile):
        """Create shapefile of dislocation geodataframe.

        Args:
            in_gpd (object): Geodataframe of the dislocation.
            programname (str): Output directory name.
            savefile (str): Output shapefile name.

        """
        # save cen_shp_blockgroup_merged shapefile
        print(
            "GeoPackage data file saved to: " + programname + "/" + savefile + ".gpkg"
        )
        in_gpd.to_file(programname + "/" + savefile + ".gpkg", driver="GPKG")

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
        print("CSV data file saved to: " + programname + "/" + savefile + ".csv")
        in_pd[save_columns].to_csv(programname + "/" + savefile + ".csv", index=False)

    @staticmethod
    def get_features_by_fips(state_county_fips):
        """
        Downloads a GeoJSON feature collection from the NSI endpoint using the provided county FIPS code
        and returns it as a GeoDataFrame with additional columns for FIPS, state FIPS, and county FIPS.

        Args:
            state_county_fips (str): The combined state and county FIPS code (e.g., '15005').

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing the features with additional columns.
        """
        print("Requesting data for " + str(state_county_fips) + " from NSI endpoint")
        json_url = Config.NSI_URL_FIPS + str(state_county_fips)
        result = requests.get(json_url)
        result.raise_for_status()
        result_json = result.json()

        collection = FeatureCollection(result_json['features'])

        gdf = gpd.GeoDataFrame.from_features(collection['features'])
        gdf = gdf.set_crs(epsg=4326)

        gdf = DataUtil.add_columns_to_gdf(gdf, state_county_fips)

        return gdf

    @staticmethod
    def download_nsi_data_state_file(state_fips):
        """
        Downloads a zipped GeoPackage file for the given state FIPS code from the NSI endpoint.

        Args:
            state_fips (str): The state FIPS code (e.g., '29' for Missouri).

        Returns:
            None
        """
        file_name = Config.NSI_PREFIX + str(state_fips) + ".gpkg.zip"
        file_url = "%s/%s" % (Config.NSI_URL_STATE, file_name)
        print("Downloading NSI data for the state: " + str(state_fips))
        r = requests.get(file_url, stream=True)

        if r is None or r.status_code != 200:
            r.raise_for_status()

        else:
            download_filename = os.path.join("data", file_name)

            with open(download_filename, "wb") as zipfile:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        zipfile.write(chunk)
                        print("Downloading NSI data for the state: " + str(state_fips))

    @staticmethod
    def read_geopkg_to_gdf(infile):
        """
        Reads a GeoPackage file and converts it into a GeoDataFrame.

        Args:
            infile (str): Path to the GeoPackage file.

        Returns:
            gpd.GeoDataFrame: A GeoDataFrame containing data from the GeoPackage file.
        """
        print("Reading GeoPackage")
        gpkgpd = None
        for layername in fiona.listlayers(infile):
            gpkgpd = gpd.read_file(infile, layer=layername, crs='EPSG:4326')

        return gpkgpd

    @staticmethod
    def add_guid_to_gdf(gdf):
        """
        Adds a globally unique identifier (GUID) column to the GeoDataFrame.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with a new 'guid' column.
        """
        print("Creating GUID column")
        gdf['guid'] = [str(uuid.uuid4()) for _ in range(len(gdf))]

        return gdf

    @staticmethod
    def add_columns_to_gdf(gdf, fips):
        """
        Adds FIPS-related columns (FIPS, state FIPS, and county FIPS) to the GeoDataFrame.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame.
            fips (str): Combined state and county FIPS code.

        Returns:
            gpd.GeoDataFrame: GeoDataFrame with new FIPS-related columns.
        """
        print("Creating FIPS-related columns")
        statefips = fips[:2]
        countyfips = fips[2:]
        for i, row in gdf.iterrows():
            guid_val = str(uuid.uuid4())
            gdf.at[i, 'guid'] = guid_val
            gdf.at[i, 'fips'] = fips
            gdf.at[i, 'statefips'] = statefips
            gdf.at[i, 'countyfips'] = countyfips

        return gdf

    @staticmethod
    def gdf_to_geopkg(gdf, outfile):
        """
        Saves a GeoDataFrame as a GeoPackage file.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame.
            outfile (str): Path to the output GeoPackage file.

        Returns:
            None
        """
        print("Creating output GeoPackage")
        gdf.to_file(outfile, driver="GPKG")

    @staticmethod
    def upload_postgres_from_gpkg(infile):
        """
        Reads data from a GeoPackage file and uploads it to a PostgreSQL database.

        Args:
            infile (str): Path to the GeoPackage file.

        Returns:
            None
        """
        gpkgpd = None
        for layername in fiona.listlayers(infile):
            gpkgpd = gpd.read_file(infile, layer=layername, crs='EPSG:4326')

        DataUtil.upload_postgres_gdf(gpkgpd)

    @staticmethod
    def upload_postgres_gdf(gdf):
        """
        Uploads a GeoDataFrame to a PostgreSQL database.

        Args:
            gdf (gpd.GeoDataFrame): Input GeoDataFrame.

        Returns:
            bool: True if upload is successful, False otherwise.
        """
        try:
            db_connection_url = "postgresql://%s:%s@%s:%s/%s" % \
                                (Config.DB_USERNAME, Config.DB_PASSWORD, Config.DB_URL, Config.DB_PORT, Config.DB_NAME)
            con = create_engine(db_connection_url)

            print('Dropping ' + str(gdf.geometry.isna().sum()) + ' nulls.')
            gdf = gdf.dropna(subset=['geometry'])

            print('Uploading GeoDataFrame to database')
            gdf.to_postgis("nsi_raw", con, index=False, if_exists='replace')

            con.dispose()

            print('Upload to database completed.')

            return True

        except sqlalchemy.exc.OperationalError:
            print("Error in connecting to the database server")
            return False