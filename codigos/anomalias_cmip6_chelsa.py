import xarray as xr
import pandas as pd
import numpy as np
import os
import calendar

# === Paths reales
base_path = '/media/duilio/8277-C610/OGGM/insumos/CHELSA/clipped_version'
futuro_path = '/media/duilio/8277-C610/OGGM/insumos/GCM_bias_CHELSA/clipped_version'
salida_path = '/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias'

# === Basins
basins = ['fid_42', 'fid_48', 'fid_51', 'fid_56', 'fid_59', 'fid_61']

# === Resultado final
resultados_pr = []
resultados_tas = []

for basin in basins:
    print(f"Procesando {basin}...")
    # --- Cargar base histórica
    base_file_pr = os.path.join(base_path, f'CHELSA_PP_{basin}.nc')
    base_file_tas = os.path.join(base_path, f'CHELSA_T2M_{basin}.nc')

    hist_pr = xr.open_dataset(base_file_pr)
    hist_tas = xr.open_dataset(base_file_tas)

    precip_hist = hist_pr['prcp'].mean(dim=('lat', 'lon'))
    temp_hist = hist_tas['temp'].mean(dim=('lat', 'lon'))  # !! en °C ya

    precip_hist_annual = precip_hist.resample(time='A').sum()
    temp_hist_annual = temp_hist.resample(time='A').mean()

    precip_hist_period = precip_hist_annual.sel(time=slice('1980-01-01', '2010-12-31'))
    temp_hist_period = temp_hist_annual.sel(time=slice('1980-01-01', '2010-12-31'))

    precip_hist_mean_value = precip_hist_period.mean().item()
    temp_hist_mean_value = temp_hist_period.mean().item()

    # --- Buscar futuros asociados al basin
    futuros_basin_pr = [f for f in os.listdir(futuro_path) if basin in f and f.endswith('.nc') and 'PP_CHELSA' in f]
    futuros_basin_tas = [f for f in os.listdir(futuro_path) if basin in f and f.endswith('.nc') and 'T2M_CHELSA' in f]

    for futuro_file in futuros_basin_pr:
        futuro_full_path = os.path.join(futuro_path, futuro_file)
        fut = xr.open_dataset(futuro_full_path)
        precip_futuro_raw = fut['pr'].mean(dim=('lat', 'lon'))

        times = pd.to_datetime(precip_futuro_raw['time'].values)
        seconds_in_month = np.array([calendar.monthrange(t.year, t.month)[1] * 86400 for t in times])
        precip_futuro_mm = precip_futuro_raw * xr.DataArray(seconds_in_month, coords=[precip_futuro_raw['time']], dims=['time'])

        precip_futuro_annual = precip_futuro_mm.resample(time='A').sum()
        precip_futuro_period = precip_futuro_annual.sel(time=slice('2030-01-01', '2060-12-31'))
        precip_futuro_mean_value = precip_futuro_period.mean().item()

        anomaly_abs = precip_futuro_mean_value - precip_hist_mean_value
        anomaly_perc = anomaly_abs / precip_hist_mean_value

        parts = futuro_file.replace('.nc', '').split('_')
        model_name = parts[2]
        ssp = parts[3].replace('ssp', '')
        bbc = parts[4]

        resultados_pr.append({
            'basin': int(basin.split('_')[1]),
            'model': model_name,
            'ssp_list': int(ssp),
            'bbc_list': bbc,
            'Precipitation_Mean': anomaly_abs,
            'Precipitation_Mean_perc': anomaly_perc
        })

    for futuro_file in futuros_basin_tas:
        futuro_full_path = os.path.join(futuro_path, futuro_file)
        fut = xr.open_dataset(futuro_full_path)
        temp_futuro_raw = fut['tas'].mean(dim=('lat', 'lon'))

        # === Importante: Convertir de K a °C
        temp_futuro_raw_celsius = temp_futuro_raw - 273.15

        temp_futuro_annual = temp_futuro_raw_celsius.resample(time='A').mean()
        temp_futuro_period = temp_futuro_annual.sel(time=slice('2030-01-01', '2060-12-31'))
        temp_futuro_mean_value = temp_futuro_period.mean().item()

        anomaly_abs = temp_futuro_mean_value - temp_hist_mean_value
        anomaly_perc = anomaly_abs / temp_hist_mean_value

        parts = futuro_file.replace('.nc', '').split('_')
        model_name = parts[2]
        ssp = parts[3].replace('ssp', '')
        bbc = parts[4]

        resultados_tas.append({
            'basin': int(basin.split('_')[1]),
            'model': model_name,
            'ssp_list': int(ssp),
            'bbc_list': bbc,
            'Temperature_Mean': anomaly_abs,
            'Temperature_Mean_perc': anomaly_perc
        })

# --- Guardar resultados
resultados_pr_df = pd.DataFrame(resultados_pr)
resultados_tas_df = pd.DataFrame(resultados_tas)

# Guardar completos
resultados_pr_df.to_csv(os.path.join(salida_path, 'cmip6_chelsa_anomalias_pr.csv'), index=False)
resultados_tas_df.to_csv(os.path.join(salida_path, 'cmip6_chelsa_anomalias_tas.csv'), index=False)

# Guardar versión broad agrupada
resultados_pr_broad = resultados_pr_df.groupby(['basin', 'ssp_list']).agg(
    mean_precipitation=('Precipitation_Mean', 'mean'),
    std_precipitation=('Precipitation_Mean', 'std'),
    mean_precipitation_perc=('Precipitation_Mean_perc', 'mean'),
    std_precipitation_perc=('Precipitation_Mean_perc', 'std')
).reset_index()

resultados_tas_broad = resultados_tas_df.groupby(['basin', 'ssp_list']).agg(
    mean_temperature=('Temperature_Mean', 'mean'),
    std_temperature=('Temperature_Mean', 'std'),
    mean_temperature_perc=('Temperature_Mean_perc', 'mean'),
    std_temperature_perc=('Temperature_Mean_perc', 'std')
).reset_index()

resultados_pr_broad.to_csv(os.path.join(salida_path, 'cmip6_chelsa_anomalias_pr_broad_summary.csv'), index=False)
resultados_tas_broad.to_csv(os.path.join(salida_path, 'cmip6_chelsa_anomalias_tas_broad_summary.csv'), index=False)

print("✅ Resultados de precipitación y temperatura guardados correctamente, incluyendo versión broad.")
