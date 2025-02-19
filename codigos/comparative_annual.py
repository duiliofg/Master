# Reimport necessary libraries after reset
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import kendalltau
import ace_tools as tools

# File paths
files = {
    "CR2MET - SSP1-2.6": "/mnt/data/Copia de Runoff_CR2MET_CMIP6_anual_ssp126_v2.csv",
    "CR2MET - SSP5-8.5": "/mnt/data/Copia de Runoff_CR2MET_CMIP6_anual_ssp585_v2.csv",
    "CHELSA - SSP1-2.6": "/mnt/data/Runoff_CHELSA_CMIP6_anual_v2_ssp126.csv",
    "CHELSA - SSP5-8.5": "/mnt/data/Runoff_CHELSA_CMIP6_anual_v2_ssp585.csv",
    "CR2MET - CMIP5 - RCP8.5": "/mnt/data/Runoff_CR2MET_CMIP5_anual_v2.csv",
    "BH5 - CMIP5 - RCP8.5": "/mnt/data/mean_of_means_bh5_cuenca_monthly_1980_2060.csv"
}

# Dictionary to store annual mean and std
df_annual_summary = pd.DataFrame()

# Process each file
for model, path in files.items():
    df = pd.read_csv(path)

    # Ensure the correct year column
    if "Year" not in df.columns:
        if "Fecha" in df.columns:
            df["Year"] = pd.to_datetime(df["Fecha"]).dt.year

    # Ensure the correct runoff column
    runoff_col = [col for col in df.columns if "Runoff" in col or "Mean" in col]
    if runoff_col:
        df["Runoff_Total"] = df[runoff_col[0]]
    else:  # Special case for BH5 where runoff is summed from RIO columns
        rio_columns = [col for col in df.columns if "RIO" in col]
        df["Runoff_Total"] = df[rio_columns].sum(axis=1)

    # Replace negative values with 0
    df["Runoff_Total"] = df["Runoff_Total"].clip(lower=0)

    # Group by year and calculate mean and std
    df_summary = df.groupby("Year")["Runoff_Total"].agg(["mean", "std"]).reset_index()
    df_summary["Model"] = model

    # Append to the summary dataframe
    df_annual_summary = pd.concat([df_annual_summary, df_summary], ignore_index=True)

# Test de Mann-Kendall para evaluar tendencias de caudal
trend_results = []
for model in df_annual_summary["Model"].unique():
    subset = df_annual_summary[df_annual_summary["Model"] == model]
    tau, p_value = kendalltau(subset["Year"], subset["mean"])
    trend_results.append({"Model": model, "Kendall Tau": tau, "p-value": p_value})

df_mk_trends = pd.DataFrame(trend_results)

# Comparación entre modelos y escenarios
df_model_comparison = df_annual_summary.groupby("Model")["mean"].agg(["mean", "std", "min", "max"]).reset_index()

# Comparación de la variabilidad del caudal
df_variability = df_annual_summary.groupby("Model")["std"].agg(["mean"]).reset_index()
df_variability.rename(columns={"mean": "Mean Std Dev"}, inplace=True)

# Display tables for review
tools.display_dataframe_to_user(name="Mann-Kendall Trend Analysis", dataframe=df_mk_trends)
tools.display_dataframe_to_user(name="Model Scenario Comparison", dataframe=df_model_comparison)
tools.display_dataframe_to_user(name="Runoff Variability", dataframe=df_variability)

# Graficar tendencias de caudal
plt.figure(figsize=(12, 6))
for model in df_annual_summary["Model"].unique():
    subset = df_annual_summary[df_annual_summary["Model"] == model]
    plt.plot(subset["Year"], subset["mean"], label=model)

plt.xlabel("Year")
plt.ylabel("Mean Runoff (mm)")
plt.title("Annual Mean Runoff Trends Across Models")
plt.legend()
plt.grid(True)
plt.show()

# Gráfico de distribución del caudal en períodos 1980-2020 vs 2030-2060
df_annual_summary["Period"] = np.where(df_annual_summary["Year"] <= 2020, "1980-2020", "2030-2060")

plt.figure(figsize=(12, 6))
sns.boxplot(x=df_annual_summary["Year"].astype(str), y=df_annual_summary["mean"], hue=df_annual_summary["Period"])
plt.xticks(rotation=90)
plt.xlabel("Year")
plt.ylabel("Mean Runoff (mm)")
plt.title("Runoff Distribution Over Time by Period (1980-2020 vs 2030-2060)")
plt.legend(title="Period")
plt.show()
