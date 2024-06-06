import os
import geopandas as gpd
import xarray as xr
from shapely.geometry import Polygon
from geopandas.tools import overlay

def clip_netcdf_with_shapefile(netcdf_path, shapefile_path, output_path):
    print(f"Processing: {shapefile_path}")
    
    # Load the shapefile
    shapefile = gpd.read_file(shapefile_path)
    
    # Load the NetCDF file using xarray
    dataset = xr.open_dataset(netcdf_path)
    variable_name = 'temp'  # Specify the variable name (update if needed)
    dataset = dataset[variable_name]
    
    # Extract the bounding box of the shapefile
    bbox = shapefile.geometry.unary_union.bounds

    # Create a GeoDataFrame with the bounding box
    bbox_gdf = gpd.GeoDataFrame(geometry=[Polygon.from_bounds(*bbox)], crs=shapefile.crs)
    
    # Set spatial dimensions
    dataset = dataset.rio.set_spatial_dims("lon", "lat", inplace=True)

    # Set CRS for the NetCDF data variable
    dataset = dataset.rio.write_crs('EPSG:4326')

    # Use geopandas overlay to get the intersection
    intersection = overlay(bbox_gdf, shapefile, how='intersection')
    
    # Clip the NetCDF file with the intersected geometry
    clipped_data = dataset.rio.clip(intersection.geometry).load()

    # Remove the grid_mapping attribute to avoid the ValueError
    if 'grid_mapping' in clipped_data.attrs:
        del clipped_data.attrs['grid_mapping']

    # Save the clipped NetCDF file
    clipped_data.to_netcdf(output_path)
    
    # Close the datasets
    dataset.close()
    print(f"Finished processing: {shapefile_path}")

def clip_netcdf_for_all_shapefiles(netcdf_path, shapefiles_folder, output_folder, name_output):
    # Iterate over all shapefiles in the specified folder
    for shapefile_name in os.listdir(shapefiles_folder):
        if shapefile_name.endswith(".gpkg"):
            shapefile_path = os.path.join(shapefiles_folder, shapefile_name)
            
            # Construct the output path based on the shapefile name
            output_path = os.path.join(output_folder, f"{name_output}_{shapefile_name[:-4]}nc")
            
            # Clip NetCDF with the current shapefile
            clip_netcdf_with_shapefile(netcdf_path, shapefile_path, output_path)

# Specify the paths
netcdf_path = "/media/duilio/8277-C610/OGGM/insumos/CHELSA/CHELSA_OGGM_1979_2019_masked.nc"
shapefiles_folder = '/media/duilio/8277-C610/OGGM/insumos/cuencas'
output_folder = '/media/duilio/8277-C610/OGGM/insumos/CHELSA/clipped_version'
name_output = 'CHELSA_T2M'

print(name_output)
clip_netcdf_for_all_shapefiles(netcdf_path, shapefiles_folder, output_folder, name_output)
