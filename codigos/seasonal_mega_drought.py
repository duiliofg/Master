import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import f_oneway, kruskal

# Definir rutas de los archivos
file_paths = {
    "CHELSA_CMIP6_SSP126": "/mnt/data/Runoff_CHELSA_CMIP6_anual_v2_ssp126.csv",
    "CHELSA_CMIP6_SSP585": "/mnt/data/Runoff_CHELSA_CMIP6_anual_v2_ssp585.csv",
    "CR2MET_CMIP5": "/mnt/data/Runoff_CR2MET_CMIP5_anual_v2.csv",
    "CR2MET_CMIP6_SSP585": "/mnt/data/Runoff_CR2MET_CMIP6_anual_ssp585_v2.csv",
    "CR2MET_CMIP6_SSP126": "/mnt/data/Runoff_CR2MET_CMIP6_anual_ssp126_v2.csv",
}

# Cargar los archivos en dataframes
dataframes = {key: pd.read_csv(path) for key, path in file_paths.items()}

# Crear una nueva columna de estación
def get_season(month):
    if month in [12, 1, 2]:
        return "Verano (DJF)"
    elif month in [3, 4, 5]:
        return "Otoño (MAM)"
    elif month in [6, 7, 8]:
        return "Invierno (JJA)"
    else:
        return "Primavera (SON)"

# Agregar la estación a cada DataFrame
for key, df in dataframes.items():
    df["Season"] = df["Month"].apply(get_season)

# Unir todos los dataframes para análisis conjunto
seasonal_combined_df = pd.concat(dataframes.values(), keys=dataframes.keys(), names=["Dataset", "Index"]).reset_index()

# Definir los períodos a comparar
pre_megasequia_df = seasonal_combined_df[(seasonal_combined_df["Year"] >= 1980) & (seasonal_combined_df["Year"] < 2010)]
megasequia_df = seasonal_combined_df[(seasonal_combined_df["Year"] >= 2010) & (seasonal_combined_df["Year"] <= 2021)]

# Agregar una columna indicando el período
pre_megasequia_df["Period"] = "1980-2010"
megasequia_df["Period"] = "2010-2021"

# Combinar ambos períodos en un solo DataFrame
comparison_df = pd.concat([pre_megasequia_df, megasequia_df])

# Visualización: Boxplots del runoff por estación y período
plt.figure(figsize=(16, 12))
seasons = ["Verano (DJF)", "Otoño (MAM)", "Invierno (JJA)", "Primavera (SON)"]

for i, season in enumerate(seasons, 1):
    plt.subplot(2, 2, i)
    sns.boxplot(data=comparison_df[comparison_df["Season"] == season], 
                x="Period", y="Mean_Runoff", hue="Dataset")
    plt.title(f"Comparación del Runoff por Estación entre 1980-2010 y 2010-2021 ({season})")
    plt.xlabel("Periodo")
    plt.ylabel("Runoff Medio (m³/s)")
    plt.legend(title="Dataset", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True)

plt.tight_layout()
plt.show()

# Análisis estadístico por estación para comparar los períodos
period_anova_results = {}
period_kruskal_results = {}

for season in seasons:
    for dataset in dataframes.keys():
        df = comparison_df[comparison_df["Dataset"] == dataset]
        season_df = df[df["Season"] == season]

        groups = [season_df[season_df["Period"] == period]["Mean_Runoff"].dropna() for period in ["1980-2010", "2010-2021"]]

        if all(len(group) > 1 for group in groups):
            period_anova_results[(dataset, season)] = f_oneway(*groups)
            period_kruskal_results[(dataset, season)] = kruskal(*groups)

# Mostrar resultados estadísticos para la comparación entre períodos
period_anova_results, period_kruskal_results
