import pandas as pd
import numpy as np
from pymannkendall import original_test

# File paths
files = {
    "CR2MET - SSP1-2.6": "Copia de Runoff_CR2MET_CMIP6_anual_ssp126_v2.csv",
    "CR2MET - SSP5-8.5": "Copia de Runoff_CR2MET_CMIP6_anual_ssp585_v2.csv",
    "CHELSA - SSP1-2.6": "Runoff_CHELSA_CMIP6_anual_v2_ssp126.csv",
    "CHELSA - SSP5-8.5": "Runoff_CHELSA_CMIP6_anual_v2_ssp585.csv",
    "CR2MET - CMIP5 - RCP8.5": "Runoff_CR2MET_CMIP5_anual_v2.csv",
    "BH5 - CMIP5 - RCP8.5": "mean_of_means_bh5_cuenca_monthly_1980_2060.csv"
}

# Dictionary to store annual mean
df_annual_summary = pd.DataFrame()

for model, path in files.items():
    df = pd.read_csv(path)
    df["Year"] = pd.to_datetime(df.iloc[:, 0]).dt.year  # Ensure first column is year
    
    # Select runoff column
    runoff_col = [col for col in df.columns if "Runoff" in col or "Mean" in col]
    if runoff_col:
        df["Runoff_Total"] = df[runoff_col[0]]
    else:
        rio_columns = [col for col in df.columns if "RIO" in col]
        df["Runoff_Total"] = df[rio_columns].sum(axis=1)
    
    df["Runoff_Total"] = df["Runoff_Total"].clip(lower=0)  # Replace negative values
    df_summary = df.groupby("Year")["Runoff_Total"].mean().reset_index()
    df_summary["Model"] = model
    df_annual_summary = pd.concat([df_annual_summary, df_summary], ignore_index=True)

# Mann-Kendall Trend Test
mk_results = []
for model in df_annual_summary["Model"].unique():
    series = df_annual_summary[df_annual_summary["Model"] == model]["Runoff_Total"].values
    tau, p_value = original_test(series)[:2]
    mk_results.append([model, tau, p_value])

df_mk = pd.DataFrame(mk_results, columns=["Model", "Kendall Tau", "p-value"])

# Peak Water
df_peak = df_annual_summary.loc[df_annual_summary.groupby("Model")["Runoff_Total"].idxmax()]

# Reduction analysis using first and last 10 years
min_year, max_year = df_annual_summary["Year"].min(), df_annual_summary["Year"].max()
first_10, last_10 = list(range(min_year, min_year + 10)), list(range(max_year - 9, max_year + 1))

df_differences = df_annual_summary.groupby("Model").agg(
    initial_runoff=("Runoff_Total", lambda x: x[df_annual_summary["Year"].isin(first_10)].mean()),
    final_runoff=("Runoff_Total", lambda x: x[df_annual_summary["Year"].isin(last_10)].mean()),
    mean_runoff=("Runoff_Total", "mean")
).reset_index()

df_differences["reduction (%)"] = (
    (df_differences["initial_runoff"] - df_differences["final_runoff"]) / df_differences["initial_runoff"]) * 100

# Standard Deviation for reduction percentage
df_std = df_annual_summary.groupby("Model").agg(
    initial_std=("Runoff_Total", lambda x: x[df_annual_summary["Year"].isin(first_10)].std()),
    final_std=("Runoff_Total", lambda x: x[df_annual_summary["Year"].isin(last_10)].std())
).reset_index()

df_differences = df_differences.merge(df_std, on="Model")
df_differences["reduction_std"] = (
    ((df_differences["initial_std"]**2 + df_differences["final_std"]**2) ** 0.5) / df_differences["initial_runoff"]) * 100

# Print final tables
df_mk.to_csv("mann_kendall_results.csv", index=False)
df_peak.to_csv("peak_water_results.csv", index=False)
df_differences.to_csv("runoff_reduction_results.csv", index=False)
