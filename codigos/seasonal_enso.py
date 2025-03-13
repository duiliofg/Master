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

# Definir períodos de ENSO
enso_events = {
    "El Niño": [
        (1982, 1983), (1986, 1988), (1991, 1992), (1994, 1995),
        (1997, 1998), (2002, 2003), (2004, 2005), (2006, 2007),
        (2009, 2010), (2014, 2016), (2018, 2019), (2023, 2024)
    ],
    "La Niña": [
        (1983, 1984), (1984, 1985), (1988, 1989), (1995, 1996),
        (1998, 2001), (2005, 2006), (2007, 2008), (2008, 2009),
        (2010, 2012), (2016, 2017), (2017, 2018), (2020, 2023)
    ]
}

# Función para asignar ENSO
def assign_enso_category(year):
    for event, periods in enso_events.items():
        for start, end in periods:
            if start <= year <= end:
                return event
    return "Neutral"

# Agregar ENSO a cada DataFrame
for key, df in dataframes.items():
    df["ENSO"] = df["Year"].apply(assign_enso_category)

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

# Boxplots de runoff por estación y ENSO
plt.figure(figsize=(16, 12))
seasons = ["Verano (DJF)", "Otoño (MAM)", "Invierno (JJA)", "Primavera (SON)"]

for i, season in enumerate(seasons, 1):
    plt.subplot(2, 2, i)
    sns.boxplot(data=seasonal_combined_df[seasonal_combined_df["Season"] == season], 
                x="ENSO", y="Mean_Runoff", hue="Dataset")
    plt.title(f"Distribución del Runoff por ENSO en {season}")
    plt.xlabel("Fase ENSO")
    plt.ylabel("Runoff Medio (m³/s)")
    plt.legend(title="Dataset", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True)

plt.tight_layout()
plt.show()

# Análisis estadístico por estación
seasonal_anova_results = {}
seasonal_kruskal_results = {}

for season in seasons:
    for dataset in dataframes.keys():
        df = dataframes[dataset]
        season_df = df[df["Season"] == season]
        groups = [season_df[season_df["ENSO"] == phase]["Mean_Runoff"].dropna() for phase in ["El Niño", "La Niña", "Neutral"]]

        if all(len(group) > 1 for group in groups):
            seasonal_anova_results[(dataset, season)] = f_oneway(*groups)
            seasonal_kruskal_results[(dataset, season)] = kruskal(*groups)

# Mostrar resultados estadísticos
seasonal_anova_results, seasonal_kruskal_results
