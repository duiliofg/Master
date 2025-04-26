# CMIP6 POR CUENCA ANOMALIAS CHELSA
import pandas as pd
import xarray as xr
import os       
import numpy as np
import matplotlib.pyplot as plt
from itertools import product
import pandas as pd
import calendar
import xarray as xr
import cftime

def convert_precipitation_flux_to_mm_per_year(flux_data):
    """
    Convierte un xarray.DataArray mensual de precipitación en flujo (kg/m²/s)
    a precipitación acumulada anual (mm/año).
    """

    # Crear array de segundos por mes
    seconds_in_month = pd.Series(
        [calendar.monthrange(pd.Timestamp(t).year, pd.Timestamp(t).month)[1] * 86400 for t in flux_data['time'].values],
        index=flux_data['time'].values
    )

    # Multiplicar flujo (kg/m²/s) por segundos de cada mes
    flux_data_mm_month = flux_data * xr.DataArray(seconds_in_month.values, coords=[flux_data['time']], dims=["time"])

    # Sumar meses para obtener acumulado anual
    precip_annual = flux_data_mm_month.resample(time='A').sum()

    return precip_annual

def k_to_c(kelvin):
    celsius = kelvin - 273.15
    return celsius

def remove_outliers_xarray(data):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return data.where((data >= lower_bound) & (data <= upper_bound))

# Load the data
basins = ['fid_42', 'fid_48', 'fid_51', 'fid_56', 'fid_59', 'fid_61']
modelos = ['CCSM4', 'CSIRO4', 'IPSL', 'MIROC']
suffix = 'anomalia_2030_2060'
normal_period = slice('1980', '2010')
anomaly_period = slice('2030', '2060')
summary_pr=[]
summary_tas=[]

# Loop for basins
for basin in basins:
    tas_path = f'/media/duilio/8277-C610/OGGM/insumos/CR2MET25/clipped_version_v2/CR2MET_tas_{basin}.nc'
    pr_path = f'/media/duilio/8277-C610/OGGM/insumos/CR2MET25/clipped_version_v2/CR2MET_pr_{basin}.nc'
    data_tas = xr.open_dataset(tas_path)
    data_pr = xr.open_dataset(pr_path)

    # Extract temperature and precipitation data
    temperature_base = data_tas['temp']
    precipitation_base = data_pr['prcp']

    # Create an empty DataFrame to store summary statistics
    summary_df_tas = pd.DataFrame(columns=['Model', 'Temperature_Mean', 'Temperature_Std', 'Temperature_Min', 'Temperature_Max'])
    summary_df_pr = pd.DataFrame(columns=['Model', 'Precipitation_Mean', 'Precipitation_Mean_perc', 'Precipitation_Std', 'Precipitation_Min', 'Precipitation_Max'])

    mean_temp = temperature_base.mean(dim=('lat', 'lon'))
    mean_prep = precipitation_base.mean(dim=('lat', 'lon'))
    
    normal_temperature = mean_temp.sel(time=normal_period).resample(time='A').mean()
    # Normal histórico (1980-2010) - lo calculas una vez por basin
    mean_prep = precipitation_base.mean(dim=('lat', 'lon'))
    normal_precipitation = mean_prep.sel(time=slice('1980-01-01', '2010-12-31')).resample(time='A').sum()
    normal_precipitation_ref = normal_precipitation.mean().item()
    # Convert to pandas DataFrame
    normal_temperature = normal_temperature.to_dataframe(name='temp[°C]')
    normal_precipitation = normal_precipitation.to_dataframe(name='prep[mm]')
    
    normal_temperature.reset_index(inplace=True)
    normal_precipitation.reset_index(inplace=True)

    normal_temperature.set_index('time', inplace=True)
    normal_precipitation.set_index('time', inplace=True)

    normal_temperature['Period'] = pd.cut(normal_temperature.index.year, bins=[1980, 2010], labels=['1980-2010'])
    normal_precipitation['Period'] = pd.cut(normal_precipitation.index.year, bins=[1980, 2010], labels=['1980-2010'])

    normal_temperature = normal_temperature.dropna(subset=['Period'])
    normal_precipitation = normal_precipitation.dropna(subset=['Period'])

    directory = '/media/duilio/8277-C610/OGGM/insumos/GCM_cr2met_corregido/clipped_version'
    suffix_nc = 'PP'
    bbc_list = ['MVA', 'MBC', 'DQM']
    ssp_list = ['ssp126', 'ssp585']

    combinations = list(product(bbc_list, ssp_list, ['PP'], basin))

    # List comprehension to filter files based on combinations
    precipitation_files = [
        f for f in os.listdir(directory)
        if any(bbc in f and ssp in f and 'PP' in f and b in f for bbc, ssp, _, b in combinations) and f.endswith(".nc")
    ]
    del combinations

    combinations = list(product(bbc_list, ssp_list, ['T2M'], basin))

    temperature_files =  [
        f for f in os.listdir(directory)
        if any(bbc in f and ssp in f and 'T2M' in f and b in f for bbc, ssp, _, b in combinations) and f.endswith(".nc")
    ]
    # Loop through precipitation files
    for file_pr in precipitation_files:
   # === 1. Abrir el archivo de anomalía
        file_anomaly_pr = f'{directory}/{file_pr}'
        if f'_{basin}.nc' not in file_tas:
            continue
        pr_anomaly = xr.open_dataset(file_anomaly_pr, decode_times=True)

        # === 2. Extraer precipitación
        precipitation_anomaly_data = pr_anomaly['pr']

        # === 3. Promediar espacialmente (lat, lon)
        mean_prep_anomaly = precipitation_anomaly_data.mean(dim=('lat', 'lon'))

        # === 4. Convertir de flujo (kg/m²/s) a mm/mes
        times_anomaly = pd.to_datetime(mean_prep_anomaly['time'].values)
        seconds_in_month_anomaly = np.array([calendar.monthrange(t.year, t.month)[1] * 86400 for t in times_anomaly])

        mean_prep_anomaly_mm = mean_prep_anomaly * xr.DataArray(
            seconds_in_month_anomaly,
            coords=[mean_prep_anomaly['time']],
            dims=["time"]
        )

        # === 5. Sumar los meses para obtener precipitación anual (mm/año)
        precipitation_anomaly_annual = mean_prep_anomaly_mm.resample(time='A').sum()

        # === 6. Seleccionar solo el periodo 2030-2060
        precipitation_anomaly_selected = precipitation_anomaly_annual.sel(time=slice('2030-01-01', '2060-12-31'))

        # === 7. Calcular el promedio futuro 2030-2060
        precipitation_future_mean = precipitation_anomaly_selected.mean().item()

        # === 8. Calcular la anomalía absoluta y porcentual respecto al periodo base
        # (este valor ya debe haberse calculado antes del loop para cada basin como 'normal_precipitation_ref')
        precipitation_anomaly_value = precipitation_future_mean - normal_precipitation_ref
        precipitation_anomaly_perc = precipitation_anomaly_value / normal_precipitation_ref

        # === 9. Guardar en tu resumen
        modelo_pr = file_pr[:-3]

        summary_df_pr = summary_df_pr.append({
            'Model': modelo_pr,
            'Precipitation_Mean': float(precipitation_anomaly_value),
            'Precipitation_Mean_perc': float(precipitation_anomaly_perc),
            'Precipitation_Std': float(precipitation_anomaly_selected.std().item()),
            'Precipitation_Min': float(precipitation_anomaly_selected.min().item()),
            'Precipitation_Max': float(precipitation_anomaly_selected.max().item())
        }, ignore_index=True)

    
    for file_tas in temperature_files:
        file_anomaly_tas = f'{directory}/{file_tas}'
        if f'_{basin}.nc' not in file_tas:
            continue
        tas_anomaly = xr.open_dataset(file_anomaly_tas, decode_times=False)
        tas_anomaly['time'] = xr.cftime_range(start='1980-01', periods=len(tas_anomaly['time']), freq='MS')
        
        # Extract temperature anomaly data
        temperature_anomaly_data = tas_anomaly['tas']
        mean_temp_anomaly = temperature_anomaly_data.mean(dim=('lat', 'lon'))
        temperature_anomaly_data = mean_temp_anomaly.resample(time='A').mean()
        temperature_anomaly_data = temperature_anomaly_data.loc[anomaly_period]
        temperature_anomaly_data = temperature_anomaly_data.to_dataframe(name='temp[°C]')
        
        temperature_anomaly_data.reset_index(inplace=True)
        temperature_anomaly_data.set_index('time', inplace=True)
        
        # Convert temperature anomaly from K to °C
        temperature_anomaly = (temperature_anomaly_data.mean() - normal_temperature.mean()) - 273.15
        temperature_anomaly_perc = (temperature_anomaly_data.mean() - normal_temperature.mean()) / normal_temperature.mean()
        modelo_tas = file_tas[:-3]
        
        # Append summary statistics to the DataFrame
        summary_df_tas = summary_df_tas.append({
            'Model': modelo_tas,
            'Temperature_Mean': float(temperature_anomaly.mean()),
            'Temperature_Mean_perc': float(temperature_anomaly_perc.mean()),
            'Temperature_Std': float(temperature_anomaly.std()),
            'Temperature_Min': float(temperature_anomaly.min()) if not temperature_anomaly.isnull().all() else None,
            'Temperature_Max': float(temperature_anomaly.max()) if not temperature_anomaly.isnull().all() else None
        }, ignore_index=True)            

    # Create separate DataFrames for each SSP scenario
    summary_df_pr_ssp126 = summary_df_pr[summary_df_pr['Model'].str.contains('ssp126')]
    summary_df_pr_ssp585 = summary_df_pr[summary_df_pr['Model'].str.contains('ssp585')]

    summary_df_tas_ssp126 = summary_df_tas[summary_df_tas['Model'].str.contains('ssp126')]
    summary_df_tas_ssp585 = summary_df_tas[summary_df_tas['Model'].str.contains('ssp585')]

    # Save the summary DataFrames for SSP126 and SSP585
    summary_df_pr_ssp126.to_csv(f'/media/duilio/8277-C610/OGGM/Thesis/tex/CMIP6_CR2MET_corrected_PP_ssp126_2030_2060_{basin}.csv', index=False)
    summary_df_pr_ssp585.to_csv(f'/media/duilio/8277-C610/OGGM/Thesis/tex/CMIP6_CR2MET_corrected_PP_ssp585_2030_2060_{basin}.csv')

    summary_df_tas_ssp126.to_csv(f'/media/duilio/8277-C610/OGGM/Thesis/tex/CMIP6_CR2MET_corrected_T2M_ssp126_2030_2060_{basin}.csv', index=False)
    summary_df_tas_ssp585.to_csv(f'/media/duilio/8277-C610/OGGM/Thesis/tex/CMIP6_CR2MET_corrected_T2M_ssp585_2030_2060_{basin}.csv')

    summary_pr.append(summary_df_pr_ssp126)
    summary_pr.append(summary_df_pr_ssp585)
    summary_tas.append(summary_df_tas_ssp126)
    summary_tas.append(summary_df_tas_ssp585)

summary_pr=pd.concat(summary_pr)
summary_tas=pd.concat(summary_tas)

# Extraer las categorías de interés del nombre del modelo
summary_pr['basin'] = summary_pr['Model'].str.extract(r'fid_(\d+)').astype(int)
summary_pr['ssp_list'] = summary_pr['Model'].str.extract(r'ssp(\d+)').astype(int)
summary_pr['bbc_list'] = summary_pr['Model'].str.extract(r'(MVA|MBC|DQM)').astype(str)

# Calcular el promedio y la desviación estándar
resultados_pr = summary_pr.groupby(['basin', 'ssp_list', 'bbc_list']).agg({
    'Precipitation_Mean': ['mean', 'std'],
    'Precipitation_Mean_perc': ['mean', 'std']
}).reset_index()

resultados_pr_broad = summary_pr.groupby(['basin', 'ssp_list']).agg({
    'Precipitation_Mean': ['mean', 'std'],
    'Precipitation_Mean_perc': ['mean', 'std']
}).reset_index()



# Extraer las categorías de interés del nombre del modelo
summary_tas['basin'] = summary_tas['Model'].str.extract(r'fid_(\d+)').astype(int)
summary_tas['ssp_list'] = summary_tas['Model'].str.extract(r'ssp(\d+)').astype(int)
summary_tas['bbc_list'] = summary_tas['Model'].str.extract(r'(MVA|MBC|DQM)').astype(str)

# Calcular el promedio y la desviación estándar
resultados_tas = summary_tas.groupby(['basin', 'ssp_list', 'bbc_list']).agg({
    'Temperature_Mean': ['mean', 'std'],
    'Temperature_Mean_perc': ['mean', 'std']
}).reset_index()
resultados_tas_broad = summary_tas.groupby(['basin', 'ssp_list']).agg({
    'Temperature_Mean': ['mean', 'std'],
    'Temperature_Mean_perc': ['mean', 'std']
}).reset_index()

resultados_pr_broad.columns = ['_'.join(col).strip('_') for col in resultados_pr_broad.columns.values]
resultados_tas_broad.columns = ['_'.join(col).strip('_') for col in resultados_tas_broad.columns.values]


resultados_pr.to_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/cmip6_cr2met_anomalias_pr.csv', index=False)
resultados_tas.to_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/cmip6_cr2met_anomalias_tas.csv', index=False)
resultados_pr_broad.to_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/cmip6_cr2met_anomalias_pr_broad.csv', index=False)
resultados_tas_broad.to_csv('/media/duilio/8277-C610/OGGM/Thesis/tex/anomalias/cmip6_cr2met_anomalias_tas_broad.csv', index=False)

