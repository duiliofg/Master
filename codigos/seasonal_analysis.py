import pandas as pd
import ace_tools as tools  # Import necessary tool for displaying data

# Define file paths
files = {
    "BH5_CMIP5": "/mnt/data/BH5_CMIP5_Combined.csv",
    "CR2MET_CMIP6_SSP126": "/mnt/data/CR2MET_CMIP6_ssp126_Runoff_Combined.csv",
    "CR2MET_CMIP6_SSP585": "/mnt/data/CR2MET_CMIP6_ssp585_Runoff_Combined.csv",
    "CHELSA_SSP126": "/mnt/data/Runoff_CHELSA_ssp126_Combined.csv",
    "CHELSA_SSP585": "/mnt/data/Runoff_CHELSA_ssp585_Combined.csv",
    "CR2MET_CMIP5": "/mnt/data/Runoff_CR2MET_CMIP5_Combined.csv"
}

# Define catchment names
catchment_mapping = {54: "Aconcagua", 57: "Maipo", 60: "Rapel", 71: "Mataquito", 73: "Maule"}

# Define seasons
seasons = {
    "DJF": [12, 1, 2],
    "MAM": [3, 4, 5],
    "JJA": [6, 7, 8],
    "SON": [9, 10, 11]
}

# Process all files
seasonal_means = []
for scenario, filepath in files.items():
    df = pd.read_csv(filepath)
    df.rename(columns={"COD_CUEN": "Cuenca"}, inplace=True)
    df = df[df["Cuenca"].isin(catchment_mapping.keys())]
    df["Cuenca"] = df["Cuenca"].map(catchment_mapping)

    for (decade, cuenca), group in df.groupby(["Decade", "Cuenca"]):
        for season_name, months in seasons.items():
            subset = group[group["Month"].isin(months)]
            mean_value = subset["Mean"].mean()
            std_value = (subset["Std"] ** 2).sum() ** 0.5 / len(months)  # Propagation of uncertainty
            seasonal_means.append([scenario, decade, cuenca, season_name, mean_value, std_value])

# Create DataFrame with seasonal statistics
seasonal_df = pd.DataFrame(seasonal_means, columns=["Escenario", "Decade", "Cuenca", "Estación", "Mean", "Std"])

# Calculate percentage differences and absolute changes
seasonal_df_1980_2020 = seasonal_df[seasonal_df["Decade"] == "1980-2020"].set_index(["Escenario", "Cuenca", "Estación"])
seasonal_df_2030_2060 = seasonal_df[seasonal_df["Decade"] == "2030-2060"].set_index(["Escenario", "Cuenca", "Estación"])

percentage_difference = ((seasonal_df_2030_2060["Mean"] - seasonal_df_1980_2020["Mean"]) / seasonal_df_1980_2020["Mean"]) * 100
std_propagated = ((seasonal_df_1980_2020["Std"] ** 2 + seasonal_df_2030_2060["Std"] ** 2) ** 0.5 / seasonal_df_1980_2020["Mean"]) * 100
absolute_change = seasonal_df_2030_2060["Mean"] - seasonal_df_1980_2020["Mean"]
std_absolute_propagated = (seasonal_df_1980_2020["Std"] ** 2 + seasonal_df_2030_2060["Std"] ** 2) ** 0.5

# Create final table with formatted results
final_seasonal_df = pd.DataFrame({
    "Escenario": seasonal_df_1980_2020.index.get_level_values(0),
    "Cuenca": seasonal_df_1980_2020.index.get_level_values(1),
    "Estación": seasonal_df_1980_2020.index.get_level_values(2),
    "Mean (1980-2020) ± Std": seasonal_df_1980_2020["Mean"].round(2).astype(str) + " ± " + seasonal_df_1980_2020["Std"].round(2).astype(str),
    "Mean (2030-2060) ± Std": seasonal_df_2030_2060["Mean"].round(2).astype(str) + " ± " + seasonal_df_2030_2060["Std"].round(2).astype(str),
    "Percentage Difference ± Std": percentage_difference.round(2).astype(str) + " ± " + std_propagated.round(2).astype(str),
    "Absolute Change (m³/s) ± Std": absolute_change.round(2).astype(str) + " ± " + std_absolute_propagated.round(2).astype(str)
}).reset_index(drop=True)

# Separate results by watershed
for cuenca in final_seasonal_df["Cuenca"].unique():
    cuenca_df = final_seasonal_df[final_seasonal_df["Cuenca"] == cuenca]
    tools.display_dataframe_to_user(name=f"Seasonal Runoff Changes - {cuenca}", dataframe=cuenca_df)
