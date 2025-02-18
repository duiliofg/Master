# File paths
files = {
    "CR2MET - SSP1-2.6": "/mnt/data/Runoff_CR2MET_CMIP6_anual_ssp126_v2.csv",
    "CR2MET - SSP5-8.5": "/mnt/data/Runoff_CR2MET_CMIP6_anual_ssp585_v2.csv",
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

# Display updated summary
tools.display_dataframe_to_user(name="Updated Annual Runoff Summary", dataframe=df_annual_summary)

# Plot updated annual mean runoff for each model
plt.figure(figsize=(12, 6))
for model in df_annual_summary["Model"].unique():
    subset = df_annual_summary[df_annual_summary["Model"] == model]
    plt.plot(subset["Year"], subset["mean"], label=model)

plt.xlabel("Year")
plt.ylabel("Mean Runoff (mm)")
plt.title("Annual Mean Runoff Comparison Across Models and Scenarios (Updated)")
plt.legend()
plt.grid(True)
plt.show()

# Plot updated standard deviation to analyze variability
plt.figure(figsize=(12, 6))
for model in df_annual_summary["Model"].unique():
    subset = df_annual_summary[df_annual_summary["Model"] == model]
    plt.plot(subset["Year"], subset["std"], label=model)

plt.xlabel("Year")
plt.ylabel("Standard Deviation of Runoff")
plt.title("Annual Runoff Variability Across Models and Scenarios (Updated)")
plt.legend()
plt.grid(True)
plt.show()
