#Clip de datos meteorologicos por cuenca para GCM

import os
import geopandas as gpd
import xarray as xr
from shapely.geometry import Polygon
from geopandas.tools import overlay
from glob import glob
import pandas as pd 

#folder_path = "/media/duilio/8277-C610/OGGM/insumos/GCM_BH5/input_cluster/analisis_data/bias_corrected"
folder_path = "/media/duilio/8277-C610/OGGM/insumos/GCM_BH5/input_cluster/original"
# Define the file pattern to match
#file_pattern = os.path.join(folder_path, "*PP*.nc")
#file_pattern = os.path.join(folder_path, "*pr*.nc")
file_pattern = os.path.join(folder_path, "*pr*.nc")


# Use glob to find files matching the pattern
netcdf_files_path = glob(file_pattern)

# Print the list of NetCDF files

def manual_decode_time_units(dataset, units, reference_date):
    # Convert time units 'months since' to a numerical array representing the total number of days
    if units == 'months since':
        months = dataset['time'].values  # Assuming time values are stored as integers (e.g., 1, 2, 3, ...)
        # Convert months to days (approximation: each month considered as 30 days)
        days = months * 30
        # Create a pandas date range starting from reference date for the total number of days
        decoded_time = pd.date_range(start=reference_date, periods=len(days), freq='D')
        dataset['time'] = ('time', decoded_time)
    return dataset


def clip_netcdf_with_shapefile(netcdf_path, shapefile_path, output_path):
    print(f"Processing: {shapefile_path}")
    
    # Load the shapefile
    shapefile = gpd.read_file(shapefile_path)
    
    # Load the NetCDF file using xarray
    dataset = xr.open_dataset(netcdf_path,decode_times=False)
    
    dataset = manual_decode_time_units(dataset, 'months since', '2020-01-31')

    # Extract the bounding box of the shapefile
    bbox = shapefile.geometry.unary_union.bounds

    # Create a GeoDataFrame with the bounding box
    bbox_gdf = gpd.GeoDataFrame(geometry=[Polygon.from_bounds(*bbox)], crs=shapefile.crs)
    
    # Set spatial dimensions
    dataset= dataset.rio.set_spatial_dims("lon","lat", inplace=True)

    # Set CRS for the NetCDF data variable
    dataset=dataset.rio.write_crs('EPSG:4326')

    # Use geopandas overlay to get the intersection
    intersection = overlay(bbox_gdf, shapefile, how='intersection')
    
    # Clip the NetCDF file with the intersected geometry
    clipped_data = dataset.rio.clip(intersection.geometry).load()

    # Save the clipped NetCDF file
    clipped_data.to_netcdf(output_path)
    
    # Close the datasets
    dataset.close()
    print(f"Finished processing: {shapefile_path}")


def clip_netcdf_for_all_shapefiles(netcdf_path, shapefiles_folder, output_folder,name_output):
    # Iterate over all shapefiles in the specified folder
    for shapefile_name in os.listdir(shapefiles_folder):
        if shapefile_name.endswith(".gpkg"):
            shapefile_path = os.path.join(shapefiles_folder, shapefile_name)
            
            # Construct the output path based on the shapefile name
            output_path = os.path.join(output_folder, f"{name_output}_{shapefile_name[:-5]}.nc")
            
            # Clip NetCDF with the current shapefile
            clip_netcdf_with_shapefile(netcdf_path, shapefile_path, output_path)

# Specify the paths
shapefiles_folder = '/media/duilio/8277-C610/OGGM/insumos/cuencas'
#output_folder = '/media/duilio/8277-C610/OGGM/insumos/GCM_BH5/input_cluster/analisis_data/bias_corrected/clipped_version'
output_folder = '/media/duilio/8277-C610/OGGM/insumos/GCM_BH5/input_cluster/original/original_clipped'
import re

def extract_file_names(input_string):
    pattern = r'/([^/]+)\.nc'
    matches = re.findall(pattern, input_string)
    return matches



# Clip NetCDF for all shapefiles in the folde
for netcdf_file in netcdf_files_path:
    print(netcdf_file)
   #name_output=str(netcdf_file[65:-3])
    name_output=extract_file_names(netcdf_file)
    name_output=name_output[0]
    print(name_output)
    clip_netcdf_for_all_shapefiles(netcdf_file, shapefiles_folder, output_folder,name_output)

