# === CMIP6 CR2MET corregido - flujo completo corregido ===

import pandas as pd
import xarray as xr
import numpy as np
import os
import calendar

def k_to_c(kelvin):
    return kelvin - 273.15

def remove_outliers_xarray(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return data.where((data >= lower_bound) & (data <= upper_bound))

# === Paths
base_path = '/media/duilio/8277-C610/OGGM/insumos/CR2MET25/clipped_version_v2'
futuro_path = '/media/duilio/8277-C610/OGGM/insumos/GCM_cr2met_corregido/clipped_version'
salida_path = '/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias'

# === Basins
basins = ['fid_42', 'fid_48', 'fid_51', 'fid_56', 'fid_59', 'fid_61']

# === Settings
normal_period = slice('1980', '2010')
anomaly_period = slice('2030', '2060')

summary_pr = []
summary_tas = []

for basin in basins:
    print(f"Procesando {basin}...")

    # --- Historicos
    base_tas = xr.open_dataset(os.path.join(base_path, f'CR2MET_tas_{basin}.nc'))
    base_pr = xr.open_dataset(os.path.join(base_path, f'CR2MET_pr_{basin}.nc'))

    temp_hist = base_tas['temp'].mean(dim=('lat', 'lon'))
    prcp_hist = base_pr['prcp'].mean(dim=('lat', 'lon'))

    temp_hist_annual = temp_hist.resample(time='A').mean()
    prcp_hist_annual = prcp_hist.resample(time='A').sum()

    temp_hist_period = temp_hist_annual.sel(time=normal_period)
    prcp_hist_period = prcp_hist_annual.sel(time=normal_period)

    temp_hist_mean = temp_hist_period.mean().item()
    prcp_hist_mean = prcp_hist_period.mean().item()

    # --- Futuros
    futuro_files = [f for f in os.listdir(futuro_path) if basin in f and f.endswith('.nc')]

    futuros_tas = [f for f in futuro_files if 'T2M' in f]
    futuros_pr = [f for f in futuro_files if 'PP' in f]

    for futuro in futuros_tas:
        fut = xr.open_dataset(os.path.join(futuro_path, futuro), decode_times=True)
        if not np.issubdtype(fut['time'].dtype, np.datetime64):
            fut['time'] = pd.to_datetime(fut['time'].values)

        temp_fut = fut['tas'].mean(dim=('lat', 'lon'))
        temp_fut_annual = temp_fut.resample(time='A').mean()
        temp_fut_period = temp_fut_annual.sel(time=anomaly_period)

        temp_fut_mean = temp_fut_period.mean().item() - 273.15
        anomaly_abs = temp_fut_mean - temp_hist_mean
        anomaly_perc = anomaly_abs / temp_hist_mean

        model_name = futuro.replace('.nc', '').split('_')[2]
        ssp = futuro.split('_')[3].replace('ssp', '')
        bias = futuro.split('_')[4]

        summary_tas.append({
            'basin': int(basin.split('_')[1]),
            'model': model_name,
            'ssp_list': int(ssp),
            'bbc_list': bias,
            'Temperature_Mean': anomaly_abs,
            'Temperature_Mean_perc': anomaly_perc
        })

    for futuro in futuros_pr:
        fut = xr.open_dataset(os.path.join(futuro_path, futuro), decode_times=True)
        if not np.issubdtype(fut['time'].dtype, np.datetime64):
            fut['time'] = pd.to_datetime(fut['time'].values)

        prcp_fut = fut['pr'].mean(dim=('lat', 'lon'))

        times = pd.to_datetime(prcp_fut['time'].values)
        seconds_in_month = np.array([calendar.monthrange(t.year, t.month)[1] * 86400 for t in times])

        prcp_fut_mm = prcp_fut * xr.DataArray(seconds_in_month, coords=[prcp_fut['time']], dims=['time'])
        prcp_fut_annual = prcp_fut_mm.resample(time='A').sum()
        prcp_fut_period = prcp_fut_annual.sel(time=anomaly_period)

        prcp_fut_mean = prcp_fut_period.mean().item()
        anomaly_abs = prcp_fut_mean - prcp_hist_mean
        anomaly_perc = anomaly_abs / prcp_hist_mean

        model_name = futuro.replace('.nc', '').split('_')[2]
        ssp = futuro.split('_')[3].replace('ssp', '')
        bias = futuro.split('_')[4]

        summary_pr.append({
            'basin': int(basin.split('_')[1]),
            'model': model_name,
            'ssp_list': int(ssp),
            'bbc_list': bias,
            'Precipitation_Mean': anomaly_abs,
            'Precipitation_Mean_perc': anomaly_perc
        })

# === Guardar resultados
summary_pr_df = pd.DataFrame(summary_pr)
summary_tas_df = pd.DataFrame(summary_tas)

summary_pr_df.to_csv(os.path.join(salida_path, 'cmip6_cr2met_anomalias_pr_full.csv'), index=False)
summary_tas_df.to_csv(os.path.join(salida_path, 'cmip6_cr2met_anomalias_tas_full.csv'), index=False)

# === Agrupar versión broad
broad_pr = summary_pr_df.groupby(['basin', 'ssp_list']).agg(
    mean_precipitation=('Precipitation_Mean', 'mean'),
    std_precipitation=('Precipitation_Mean', 'std'),
    mean_precipitation_perc=('Precipitation_Mean_perc', 'mean'),
    std_precipitation_perc=('Precipitation_Mean_perc', 'std')
).reset_index()

broad_tas = summary_tas_df.groupby(['basin', 'ssp_list']).agg(
    mean_temperature=('Temperature_Mean', 'mean'),
    std_temperature=('Temperature_Mean', 'std'),
    mean_temperature_perc=('Temperature_Mean_perc', 'mean'),
    std_temperature_perc=('Temperature_Mean_perc', 'std')
).reset_index()

broad_pr.to_csv(os.path.join(salida_path, 'cmip6_cr2met_anomalias_pr_broad.csv'), index=False)
broad_tas.to_csv(os.path.join(salida_path, 'cmip6_cr2met_anomalias_tas_broad.csv'), index=False)

print("\u2705 Cómputo finalizado correctamente.")
