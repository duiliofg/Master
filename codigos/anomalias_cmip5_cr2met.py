import pandas as pd
import xarray as xr
import numpy as np
import os

# Functions
def k_to_c(kelvin):
    return kelvin - 273.15

def remove_outliers_xarray(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return data.where((data >= lower_bound) & (data <= upper_bound))

# Settings
basins = ['fid_42', 'fid_48', 'fid_51', 'fid_56', 'fid_59', 'fid_61']
summary_pr = []
summary_tas = []

# Loop
for basin in basins:
    tas_path = f'/media/duilio/8277-C610/OGGM/insumos/CR2MET25/clipped_version_v2/CR2MET_tas_{basin}.nc'
    pr_path = f'/media/duilio/8277-C610/OGGM/insumos/CR2MET25/clipped_version_v2/CR2MET_pr_{basin}.nc'
    data_tas = xr.open_dataset(tas_path)
    data_pr = xr.open_dataset(pr_path)

    temp_base = data_tas['temp'].mean(dim=('lat', 'lon'))
    prcp_base = data_pr['prcp'].mean(dim=('lat', 'lon'))

    normal_temp = temp_base.sel(time=slice('1980', '2010')).resample(time='A').mean()
    normal_prcp = prcp_base.sel(time=slice('1980', '2010')).resample(time='A').sum()

    normal_temp_mean = normal_temp.mean().item()
    normal_prcp_mean = normal_prcp.mean().item()

    directory = '/media/duilio/8277-C610/OGGM/insumos/GCM_BH5/input_cluster/original/original_clipped'

    precipitation_files = [f for f in os.listdir(directory) if 'pr' in f and basin in f and f.endswith('.nc')]
    temperature_files = [f for f in os.listdir(directory) if 'tas' in f and basin in f and f.endswith('.nc')]

    for file_pr, file_tas in zip(precipitation_files, temperature_files):
        # === PRECIPITATION ===
        pr_ds = xr.open_dataset(os.path.join(directory, file_pr), decode_times=False)
        pr_ds['time'] = pd.date_range('2030-01-01', periods=len(pr_ds['time']), freq='MS')

        pr_data = pr_ds['pr'].mean(dim=('lat', 'lon'))
        pr_data = remove_outliers_xarray(pr_data)
        pr_data = pr_data.resample(time='A').sum()
        pr_data = pr_data.sel(time=slice('2030', '2060'))

        pr_anom = pr_data.mean().item() - normal_prcp_mean
        pr_anom_perc = pr_anom / normal_prcp_mean
        pr_std = pr_data.std().item()
        pr_std_perc = pr_std / normal_prcp_mean

        gcm = file_pr.split('_')[0]

        summary_pr.append({
            'basin': basin,
            'scenario': 'RCP8.5',
            'gcm': gcm,
            'Precipitation_Anomaly': pr_anom,
            'Precipitation_SD': pr_std,
            'Precipitation_Anomaly_%': pr_anom_perc * 100,
            'Precipitation_SD_%': pr_std_perc * 100
        })

        # === TEMPERATURE ===
        tas_ds = xr.open_dataset(os.path.join(directory, file_tas), decode_times=False)
        tas_ds['time'] = pd.date_range('2030-01-01', periods=len(tas_ds['time']), freq='MS')

        tas_data = tas_ds['tas'].mean(dim=('lat', 'lon'))
        tas_data = remove_outliers_xarray(tas_data)
        tas_data = tas_data.resample(time='A').mean()
        tas_data = tas_data.sel(time=slice('2030', '2060'))

        tas_anom = k_to_c(tas_data.mean().item()) - k_to_c(normal_temp_mean)
        tas_anom_perc = tas_anom / k_to_c(normal_temp_mean)
        tas_std = tas_data.std().item()
        tas_std_perc = tas_std / k_to_c(normal_temp_mean)

        summary_tas.append({
            'basin': basin,
            'scenario': 'RCP8.5',
            'gcm': gcm,
            'Temperature_Anomaly': tas_anom,
            'Temperature_SD': tas_std,
            'Temperature_Anomaly_%': tas_anom_perc * 100,
            'Temperature_SD_%': tas_std_perc * 100
        })

# Crear DataFrames
summary_pr_df = pd.DataFrame(summary_pr)
summary_tas_df = pd.DataFrame(summary_tas)

# Calcular versión BROAD (promedio de GCMs)
summary_pr_broad = summary_pr_df.groupby(['basin', 'scenario']).agg({
    'Precipitation_Anomaly': ['mean', 'std'],
    'Precipitation_Anomaly_%': ['mean', 'std']
}).reset_index()
summary_pr_broad.columns = ['basin', 'scenario', 'Precipitation_Anomaly_Mean', 'Precipitation_Anomaly_SD', 'Precipitation_Anomaly_%_Mean', 'Precipitation_Anomaly_%_SD']

summary_tas_broad = summary_tas_df.groupby(['basin', 'scenario']).agg({
    'Temperature_Anomaly': ['mean', 'std'],
    'Temperature_Anomaly_%': ['mean', 'std']
}).reset_index()
summary_tas_broad.columns = ['basin', 'scenario', 'Temperature_Anomaly_Mean', 'Temperature_Anomaly_SD', 'Temperature_Anomaly_%_Mean', 'Temperature_Anomaly_%_SD']

# === GUARDAR ===
summary_pr_df.to_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/cmip5_cr2met_precipitation_individual.csv', index=False)
summary_tas_df.to_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/cmip5_cr2met_temperature_individual.csv', index=False)
summary_pr_broad.to_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/cmip5_cr2met_precipitation_broad.csv', index=False)
summary_tas_broad.to_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/cmip5_cr2met_temperature_broad.csv', index=False)
