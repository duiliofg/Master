import pandas as pd

# Definir las estaciones del año
seasons = {
    "DJF": [12, 1, 2],  # Verano (Diciembre, Enero, Febrero)
    "MAM": [3, 4, 5],   # Otoño (Marzo, Abril, Mayo)
    "JJA": [6, 7, 8],   # Invierno (Junio, Julio, Agosto)
    "SON": [9, 10, 11]  # Primavera (Septiembre, Octubre, Noviembre)
}

# Diccionario con la relación de archivos y modelos
file_paths = {
    "BH5_CMIP5": "/mnt/data/BH5_CMIP5_Combined.csv",
    "CR2MET_SSP126": "/mnt/data/CR2MET_CMIP6_ssp126_Runoff_Combined.csv",
    "CR2MET_SSP585": "/mnt/data/CR2MET_CMIP6_ssp585_Runoff_Combined.csv",
    "CHELSA_SSP126": "/mnt/data/Runoff_CHELSA_ssp126_Combined.csv",
    "CHELSA_SSP585": "/mnt/data/Runoff_CHELSA_ssp585_Combined.csv",
    "CR2MET_RCP85": "/mnt/data/Runoff_CR2MET_CMIP5_Combined.csv",
}

# Diccionario con los códigos de cuenca y sus nombres
cuencas = {
    54: "Rio Aconcagua",
    57: "Rio Maipo",
    60: "Rio Rapel",
    71: "Rio Mataquito",
    73: "Rio Maule",
}

# Cargar los datos desde los archivos CSV
dfs = {}
for model, path in file_paths.items():
    dfs[model] = pd.read_csv(path)

# Procesar los datos estacionales
seasonal_data = []
for model, df in dfs.items():
    # Asignar la estación del año basada en el mes
    df["Season"] = df["Month"].map(
        lambda m: next((s for s, months in seasons.items() if m in months), None)
    )
    
    # Agrupar por cuenca, década y estación y calcular la media y la desviación estándar
    grouped = df.groupby(["COD_CUEN", "Decade", "Season"]).agg(
        Mean=("Mean", "mean"),
        Std=("Std", "mean")  # Se mantiene el promedio de la desviación estándar
    ).reset_index()
    
    # Asignar el modelo y el nombre de la cuenca
    grouped["Model"] = model
    grouped["Cuenca"] = grouped["COD_CUEN"].map(cuencas)
    
    seasonal_data.append(grouped)

# Concatenar todos los datos procesados en un solo DataFrame
final_df = pd.concat(seasonal_data, ignore_index=True)

# Mostrar la tabla final con los valores estacionales
print("Datos Estacionales por Cuenca y Modelo:")
print(final_df.head())

# Calcular diferencias relativas y absolutas con propagación de errores

# Filtrar la referencia (1980-2020)
reference_df = final_df[final_df["Decade"] == "1980-2020"].set_index(["COD_CUEN", "Season", "Model"])

# Filtrar las décadas futuras
future_df = final_df[final_df["Decade"] != "1980-2020"].set_index(["COD_CUEN", "Season", "Model"])

# Hacer merge entre los valores de referencia y los futuros
merged_df = future_df.join(reference_df, lsuffix='_future', rsuffix='_ref')

# Calcular diferencias absolutas y relativas
merged_df["Diff_Abs"] = merged_df["Mean_future"] - merged_df["Mean_ref"]
merged_df["Diff_Rel"] = (merged_df["Diff_Abs"] / merged_df["Mean_ref"]) * 100

# Calcular la propagación de errores
merged_df["Error_Prop"] = ((merged_df["Std_future"] ** 2 + merged_df["Std_ref"] ** 2) ** 0.5)

# Resetear el índice para visualización
diff_df = merged_df.reset_index()

# Mostrar la tabla con las diferencias relativas y absolutas
print("Diferencias Relativas y Absolutas por Cuenca y Modelo:")
print(diff_df.head())
