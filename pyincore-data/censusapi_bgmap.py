# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License v2.0 which accompanies this distribution,
# and is available at https://www.mozilla.org/en-US/MPL/2.0/

# Python packages required to read in and Census API data
import requests         # Required for the Census API
import os               # For saving output to path
import sys              # For checking version of python for replication
import pandas as pd     # For reading, writing and wrangling data
import numpy as np      # For data cleaning
import geopandas as gpd # For working with geospatial data
import folium as fm     # folium has more dynamic maps - but requires internet connection
from IPython import get_ipython

class CensusUtil():
    """Utility methods for Geospatial Visualization"""
    
    @staticmethod
    def censusapi_bgmap(state_counties, geo_name, programname):
    
        """
            Args:
                :param state_counties: List of concatenated State and County FIPS Codes
                :type state_counties: comma separated list of county fips codes
                :help state_counties: see full list https://www.nrcs.usda.gov/wps/portal/nrcs/detail/national/home/?cid=nrcs143_013697
                :param geo_name: Name of geo area - used for naming output files
                :type geo_name: String - common name of community
                :param programname: name of program used to save output files
                :type programname: string
    
            Returns:
                geopandas dataframe: Merged Block Group Level Demographic Data
                folium map: map of geodataframe
                csv file: output csv file in IN-CORE required format
                html file: output html file of folium map
                shp file: GIS shapefile of geodataframe
        """
    state_counties = ['01001','01003']
    geo_name = 'geo_name'
    # Base API URL parameters, found at https://api.census.gov/data.html
    vintage = '2010'         # Census Year
    dataset_name = 'dec/sf1' # Dataset Name
    
    # Variable parameters
    get_vars = 'GEO_ID,NAME,P005001,P005003,P005004,P005010'
    # List variables to convert from dtype object to integer
    int_vars = ['P005001','P005003','P005004','P005010']
    # GEO_ID  = Geographic ID
    # NAME    = Geographic Area Name
    # P005001 = Total
    # P005003 = Total!!Not Hispanic or Latino!!White alone
    # P005004 = Total!!Not Hispanic or Latino!!Black or African American alone
    # P005010 = Total!!Hispanic or Latino
    
    programname = 'programname'
    # Make directory to save output
    if not os.path.exists(programname):
        os.mkdir(programname)
    
    # Make a directory to save downloaded shapefiles - folder will be made then deleted
    shapefile_dir = 'shapefiletemp'
    if not os.path.exists(shapefile_dir):
        os.mkdir(shapefile_dir)
    
    # loop through counties
    appended_countydata = []  # start an empty container for the county data
    for state_county in state_counties:
        print('State_County: '+state_county)
    
        # deconcatenate state and county values
        state  = state_county[0:2]
        county = state_county[2:5]
        print('State:  '+state)
        print('County: '+county)
    
    # Set up hyperlink for Census API
    api_hyperlink = ('https://api.census.gov/data/'+vintage+'/'+dataset_name+'?get='+get_vars+
                     '&in=state:'+state+'&in=county:'+county+'&for=block%20group:*')
    print("Census API data from: "+ api_hyperlink)
    
    # Obtain Census API JSON Data
    apijson = requests.get(api_hyperlink)
    
    # Convert the requested json into pandas dataframe
    apidf = pd.DataFrame(columns=apijson.json()[0], data=apijson.json()[1:])
    
    # Append county data makes it possible to have multiple counties
    appended_countydata.append(apidf)
    
    # Create dataframe from appended county data
    cen_blockgroup = pd.concat(appended_countydata)
    
    # Add variable named "Survey" that identifies Census survey program and survey year
    cen_blockgroup['Survey'] = vintage+' '+dataset_name
    
    # Set block group FIPS code by concatenating state, county, tract and block group fips
    cen_blockgroup['bgid'] = (cen_blockgroup['state']+cen_blockgroup['county']+
                              cen_blockgroup['tract']+cen_blockgroup['block group'])
    
    # To avoid problems with how the block group id is read saving it as a string will reduce possibility for future errors
    cen_blockgroup['bgidstr'] = cen_blockgroup['bgid'].apply(lambda x : "BG"+str(x).zfill(12))
    
    # Convert variables from dtype object to integer
    for var in int_vars:
        cen_blockgroup[var] = cen_blockgroup[var].astype(int)
        print(var+' converted from object to integer')
    
    # Generate new variables
    cen_blockgroup['pwhitebg']  = cen_blockgroup['P005003'] / cen_blockgroup['P005001'] * 100
    cen_blockgroup['pblackbg']  = cen_blockgroup['P005004'] / cen_blockgroup['P005001'] * 100
    cen_blockgroup['phispbg']   = cen_blockgroup['P005010'] / cen_blockgroup['P005001'] * 100
    
    
    # ## 7. Obtain Data - Download and extract shapefiles
    # The Block Group IDs in the Census data are associated with the Block Group boundaries that can be mapped.
    # To map this data, we need the shapefile information for the block groups in the select counties.
    #
    # These files can be found online at:
    # https://www2.census.gov/geo/tiger/TIGER2010/BG/2010/
    
    # ### Download and extract shapefiles
    # Block group shapefiles are downloaded for each of the selected counties from the Census TIGER/Line Shapefiles at https://www2.census.gov/geo/tiger. Each counties file is downloaded as a zipfile and the contents are extracted. The shapefiles are reprojected to EPSG 4326 and appended as a single shapefile (as a GeoPandas GeoDataFrame) containing block groups for all of the selected counties.
    #
    # *EPSG: 4326 uses a coordinate system (Lat, Lon)
    # This coordinate system is required for mapping with folium.
    
    # loop through counties
    appended_countyshp = []  # start an empty container for the county shapefiles
    for state_county in state_counties:
    
        #county_fips = state+county
        filename = f'tl_2010_{state_county}_bg10'
    
        # Use wget to download the TIGER Shapefile for a county
        # options -quiet = turn off wget output
        # add directory prefix to save files to folder named after program name
        shapefile_url = 'https://www2.census.gov/geo/tiger/TIGER2010/BG/2010/' + filename + '.zip'
        print(('Downloading Shapefiles for State_County: '+state_county+' from: '+shapefile_url).format(filename=filename))
    
        # get_ipython().system('wget --quiet '+shapefile_url+' --directory-prefix=shapefiletemp')
    
        # import urllib
        # import time
        # max_attempts = 10
        # attempts = 0
        # sleeptime = 5
    
        # while attempts < max_attempts:
        #     time.sleep(sleeptime)
        # try:
        #     response = urllib.urlopen(shapefile_url, timeout = 5)
        #     content = response.read()
        #     f = open( "local/index.html", 'w' )
        #     f.write( content )
        #     f.close()
        #     break
        # except urllib.URLError as e:
        #     attempts += 1
        #     print(e)
    
        import urllib.request
        # with urllib.request.urlopen(shapefile_url) as f:
        #     html = f.read()
        #     html.decode('utf-8')
        zip_file = os.path.join(shapefile_dir, filename + '.zip')
        urllib.request.urlretrieve(shapefile_url, zip_file)
    
        # Use unzip to extract shapefiles from zipped file
        # get_ipython().system('unzip -o -q shapefiletemp/{filename}.zip -d shapefiletemp')
    
        from zipfile import ZipFile
        with ZipFile(zip_file, 'r') as zip_obj:
            zip_obj.extractall()
        # Read shapefile to GeoDataFrame
        gdf = gpd.read_file(f'shapefiletemp/{filename}.shp')
    
        # Set projection to EPSG 4326, which is required for folium
        gdf = gdf.to_crs(epsg=4326)
    
        # Append county data
        appended_countyshp.append(gdf)
    
    # Create dataframe from appended county data
    shp_blockgroup = pd.concat(appended_countyshp)
    
    
    # ## 8. Clean Data - Merge Census demographic data to the appended shapefiles
    
    cen_shp_blockgroup_merged = pd.merge(shp_blockgroup, cen_blockgroup,
                                         left_on='GEOID10', right_on='bgid', how='left')
    
    # ## 9. Explore Data - Map merged block group shapefile and Census data
    
    # What location should the map be centered on?
    center_x = cen_shp_blockgroup_merged.bounds.minx.mean()
    center_y = cen_shp_blockgroup_merged.bounds.miny.mean()
    
    cen_shp_blockgroup_merged_map = fm.Map(location=[center_y,center_x], zoom_start=10)
    
    # Add Percent Hispanic to Map
    fm.Choropleth(
        geo_data = cen_shp_blockgroup_merged,
        data     = cen_shp_blockgroup_merged,
        columns=['GEOID10','phispbg'],
        key_on= 'feature.properties.GEOID10',
        fill_color='YlGnBu',
        name = 'Percent Hispanic',
        legend_name='Percent Hispanic (%)'
    ).add_to(cen_shp_blockgroup_merged_map)
    
    # Add Percent Black to Map
    fm.Choropleth(
        geo_data = cen_shp_blockgroup_merged,
        data     = cen_shp_blockgroup_merged,
        columns=['GEOID10','pblackbg'],
        key_on= 'feature.properties.GEOID10',
        fill_color='YlGnBu',
        name = 'Percent Black',
        legend_name='Percent Black (%)'
    ).add_to(cen_shp_blockgroup_merged_map)
    
    fm.LayerControl().add_to(cen_shp_blockgroup_merged_map)
    
    # save output files
    savefile = programname+'_'+geo_name # set file name
    # save html map
    map_save_file = programname+'/'+savefile+'_map.html'
    print('Dynamic HTML map saved to: '+map_save_file)
    cen_shp_blockgroup_merged_map.save(map_save_file)
    
    # Set paramaters for file save
    save_columns = ['bgid','bgidstr','Survey','pblackbg','phispbg'] # set column names to save
    
    # Save cen_blockgroup dataframe with save_column variables to csv named savefile
    print('CSV data file saved to: '+programname+'/'+savefile+".csv")
    cen_blockgroup[save_columns].to_csv(programname+'/'+savefile+".csv", index=False)
    
    # save cen_shp_blockgroup_merged shapefile
    print('Shapefile data file saved to: '+programname+'/'+savefile+".shp")
    cen_shp_blockgroup_merged.to_file(programname+'/'+savefile+".shp")
    
    #return geodataframe and map
    bgmap = {} # start an empty dictionary
    bgmap['gdf'] = cen_shp_blockgroup_merged.copy()
    bgmap['map'] = cen_shp_blockgroup_merged_map
    
    bgmap

if __name__ == "__main__":
    censusapi_bgmap()
